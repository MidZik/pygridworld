from collections import namedtuple
import grpc
from queue import Queue
import shutil
import tempfile

from . import simma_pb2 as pb2, simma_pb2_grpc as pb2_grpc
from .binary import PackedSimbin

Event = namedtuple('Event', 'name, json')
RpcError = grpc.RpcError
StatusCode = grpc.StatusCode
TimelineDetails = namedtuple('TimelineDetails',
                             'timeline_id, binary_id, parent_id, head_tick, creation_timestamp, tags')
BinaryDetails = namedtuple('BinaryDetails', 'binary_id, name, creation_timestamp, description_head')


class ProcessContext:
    request_command_map = {}
    request_type = None

    def __init__(self, process_method):
        self._command_queue = Queue(maxsize=1)
        self._responses = process_method(self._request_provider())

    @classmethod
    def _make_request(cls, command):
        command_class = type(command)
        kwargs = {cls.request_command_map[command_class]: command}
        return cls.request_type(**kwargs)

    @staticmethod
    def _extract_response(response):
        """Returns (success, response_command), where response is a bool indicating if the operation
        was successful or not, and the response_command is the actual response to the command."""
        message = response.WhichOneof('message')
        return message != 'error', getattr(response, message)

    def _request_provider(self):
        command = self._command_queue.get()
        while command is not None:
            yield self._make_request(command)
            self._command_queue.task_done()
            command = self._command_queue.get()
        self._command_queue.task_done()

    def _send_command(self, command):
        self._assert_context_alive()

        self._command_queue.put(command)
        try:
            success, response = self._extract_response(next(self._responses))
            if not success:
                raise RuntimeError(f"Command error: {response.message}")
            else:
                return response
        except StopIteration:
            self._responses = None
            return None
        except grpc.RpcError:
            self._responses = None
            raise

    def _assert_context_alive(self):
        if self._responses is None:
            raise RuntimeError("Edit context is dead. Create a new context.")


class SimulatorContext(ProcessContext):
    request_type = pb2.TimelineSimulatorRequest
    request_command_map = {
        request_type.Start: 'start',
        request_type.SaveStateToPoint: 'save_state_to_point',
        request_type.MoveToTick: 'move_to_tick'
    }

    def __init__(self, stub: pb2_grpc.SimmaStub, timeline_id):
        super().__init__(stub.TimelineSimulator)

        self.address, self.user_token = self._start_simulator(timeline_id)

    def _start_simulator(self, timeline_id) -> tuple[str, str]:
        """Returns (address, user_token)"""
        response = self._send_command(pb2.TimelineSimulatorRequest.Start(timeline_id=timeline_id))
        return response.address, response.user_token

    def save_state_to_point(self) -> str:
        """Returns the tick of the new point"""
        response = self._send_command(pb2.TimelineSimulatorRequest.SaveStateToPoint())
        return response.new_tick

    def move_to_tick(self, tick: int):
        self._send_command(pb2.TimelineSimulatorRequest.MoveToTick(tick=tick))

    def disconnect(self):
        self._send_command(None)


class CreatorContext(ProcessContext):
    request_type = pb2.TimelineCreatorRequest
    request_command_map = {
        request_type.StartNew: 'start_new',
        request_type.StartExisting: 'start_existing',
        request_type.StartEditing: 'start_editing',
        request_type.StopEditing: 'stop_editing',
        request_type.LoadState: 'load_state',
        request_type.SaveToNewTimeline: 'save_to_new_timeline',
    }

    def __init__(self, stub: pb2_grpc.SimmaStub):
        super().__init__(stub.TimelineCreator)

    def start_editing(self):
        self._send_command(pb2.TimelineCreatorRequest.StartEditing())

    def stop_editing(self):
        self._send_command(pb2.TimelineCreatorRequest.StopEditing())

    def load_state(self, timeline_id):
        self._send_command(pb2.TimelineCreatorRequest.LoadState(timeline_id=timeline_id))

    def save_state_to_new_timeline(self) -> str:
        """Returns the timeline id of the new timeline"""
        response = self._send_command(pb2.TimelineCreatorRequest.SaveToNewTimeline())
        return response.new_timeline_id

    def disconnect(self):
        self._send_command(None)


class NewCreatorContext(CreatorContext):
    def __init__(self, stub: pb2_grpc.SimmaStub, binary_id, initial_timeline_id, tick):
        super().__init__(stub)
        self.creator_id, self.address, self.user_token = self._start_new_creator(binary_id, initial_timeline_id, tick)

    def _start_new_creator(self, binary_id, initial_timeline_id, tick) -> tuple[str, str, str]:
        """Returns (creator_id, address, user_token)"""
        response = self._send_command(pb2.TimelineCreatorRequest.StartNew(binary_id=binary_id,
                                                                          initial_timeline_id=initial_timeline_id,
                                                                          tick=tick))
        return response.creator_id, response.address, response.user_token


class ExistingCreatorContext(CreatorContext):
    def __init__(self, stub: pb2_grpc.SimmaStub, creator_id):
        super().__init__(stub)
        self.address, self.user_token = self._start_existing_creator(creator_id)

    def _start_existing_creator(self, creator_id) -> tuple[str, str]:
        response = self._send_command(pb2.TimelineCreatorRequest.StartExisting(creator_id=creator_id))
        return response.address, response.user_token


class Client:
    def __init__(self, address):
        self._address = address
        self._channel = grpc.insecure_channel(self._address)
        self._stub = pb2_grpc.SimmaStub(self._channel)

    def close(self):
        self._channel.close()
        self._channel = None
        self._stub = None

    def __enter__(self):
        if self._stub is None:
            raise RuntimeError("Cannot enter client context: client already closed.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_timelines(self, *, filter_parents=(), require_tags=(), disallow_tags=()):
        request = pb2.TimelinesRequest()
        request.filter_parent_ids[:] = (str(parent) if parent else "" for parent in filter_parents)
        request.require_tags[:] = require_tags
        request.disallow_tags[:] = disallow_tags

        response = self._stub.GetTimelines(request)
        return list(response.timeline_ids)

    def get_timeline_ticks(self, timeline_id) -> list[int]:
        response = self._stub.GetTimelineTicks(pb2.TimelineTicksRequest(timeline_id=timeline_id))
        return list(response.tick_list.ticks)

    def get_timeline_data(self, timeline_id, *, ticks=None, start_tick=None, end_tick=None):
        request = None
        if ticks is not None:
            tick_list = pb2.TickList(ticks=ticks)
            request = pb2.TimelineDataRequest(timeline_id=timeline_id, tick_list=tick_list)
        elif start_tick is not None:
            tick_range = pb2.TickRange(start_tick=start_tick, end_tick=end_tick)
            request = pb2.TimelineDataRequest(timeline_id=timeline_id, tick_range=tick_range)
        responses = self._stub.GetTimelineData(request)
        for response in responses:
            yield response.tick, response.data

    def get_timeline_json(self, timeline_id, *, ticks=None, start_tick=None, end_tick=None):
        if ticks is not None:
            tick_list = pb2.TickList(ticks=ticks)
            request = pb2.TimelineJsonRequest(timeline_id=timeline_id, tick_list=tick_list)
        elif start_tick is not None:
            if end_tick is None:
                end_tick = -1
            tick_range = pb2.TickRange(start_tick=start_tick, end_tick=end_tick)
            request = pb2.TimelineJsonRequest(timeline_id=timeline_id, tick_range=tick_range)
        else:
            raise ValueError("Parameters incorrect.")
        responses = self._stub.GetTimelineJson(request)
        for response in responses:
            yield response.tick, response.json

    def get_timeline_events(self, timeline_id, *, start_tick=0, end_tick=-1, event_name_filters=None):
        tick_range = pb2.TickRange(start_tick=start_tick, end_tick=end_tick)
        request = pb2.TimelineEventsRequest(timeline_id=timeline_id, tick_range=tick_range)
        if event_name_filters is not None:
            request.event_name_filters[:] = event_name_filters

        responses = self._stub.GetTimelineEvents(request)
        for response in responses:
            tick = response.tick
            events = []
            for e in response.events:
                events.append(Event(e.name, e.json))

            yield tick, events

    def timeline_simulator(self, timeline_id):
        return SimulatorContext(self._stub, timeline_id)

    def new_timeline_creator(self, binary_id, initial_timeline_id, tick):
        return NewCreatorContext(self._stub, binary_id, initial_timeline_id, tick)

    def existing_timeline_creator(self, creator_id):
        return ExistingCreatorContext(self._stub, creator_id)

    def modify_timeline_tags(self, timeline_id, *, tags_to_add=(), tags_to_remove=()):
        request = pb2.ModifyTimelineTagsRequest(timeline_id=timeline_id)
        request.tags_to_add[:] = tags_to_add
        request.tags_to_remove[:] = tags_to_remove
        self._stub.ModifyTimelineTags(request)

    def delete_timeline(self, timeline_id):
        request = pb2.DeleteTimelineRequest(timeline_id=timeline_id)
        self._stub.DeleteTimeline(request)

    def get_timeline_details(self, timeline_id: str):
        request = pb2.GetTimelineDetailsRequest(timeline_id=timeline_id)
        response = self._stub.GetTimelineDetails(request)

        return TimelineDetails(timeline_id=timeline_id,
                               binary_id=response.binary_id,
                               parent_id=response.parent_id,
                               head_tick=response.head_tick,
                               creation_timestamp=response.creation_timestamp,
                               tags=tuple(response.tags))

    def upload_packed_simbin(self, packed_simbin: PackedSimbin):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_name = shutil.make_archive(f"{temp_dir}\\packed_simbin", "zip", str(packed_simbin.path), '.')

            def reader():
                with open(archive_name, 'rb') as archive:
                    while len(data := archive.read(1_000_000)) > 0:
                        yield pb2.UploadPackedSimbinRequest(data=data)
                    yield pb2.UploadPackedSimbinRequest()

            response = self._stub.UploadPackedSimbin(reader())
        return response.binary_id

    def get_binary_details(self, binary_id: str = None):
        request = pb2.GetBinaryDetailsRequest(binary_id=binary_id)
        responses = self._stub.GetBinaryDetails(request)

        if not binary_id:
            return (BinaryDetails(binary_id=response.binary_id,
                                  name=response.name,
                                  creation_timestamp=response.creation_timestamp,
                                  description_head=response.description_head)
                    for response in responses)
        else:
            response = next(responses, None)
            if response:
                return BinaryDetails(binary_id=response.binary_id,
                                     name=response.name,
                                     creation_timestamp=response.creation_timestamp,
                                     description_head=response.description_head)
            else:
                return None

    def get_binary_description(self, binary_id: str):
        request = pb2.GetBinaryDescriptionRequest(binary_id=binary_id)
        response = self._stub.GetBinaryDescription(request)

        return response.description

    def set_binary_description(self, binary_id: str, description: str):
        request = pb2.SetBinaryDescriptionRequest(binary_id=binary_id, description=description)
        self._stub.SetBinaryDescription(request)

    def delete_binary(self, binary_id: str):
        request = pb2.DeleteBinaryRequest(binary_id=binary_id)
        self._stub.DeleteBinary(request)
