import grpc

import simma.simma_pb2 as pb2
import simma.simma_pb2_grpc as pb2_grpc
from collections import namedtuple
from queue import Queue


Event = namedtuple('Event', 'name, json')
RpcError = grpc.RpcError
StatusCode = grpc.StatusCode
TimelineDetails = namedtuple('TimelineDetails', 'binary_id, parent_id, head_tick, creation_timestamp, tags')


class SimulatorContext:
    request_command_map = {
        pb2.TimelineSimulatorRequest.Start: 'start',
        pb2.TimelineSimulatorRequest.SaveStateToPoint: 'save_state_to_point',
        pb2.TimelineSimulatorRequest.MoveToTick: 'move_to_tick'
    }

    def __init__(self, stub: pb2_grpc.SimmaStub, timeline_id):
        self._stub = stub

        self._command_queue = Queue(maxsize=1)

        self._responses = self._stub.TimelineSimulator(self._request_provider())

        success, response = self._start_simulator(timeline_id)
        if not success:
            raise RuntimeError("Failed to start simulator")
        self.address = response.address
        self.user_token = response.user_token

    @staticmethod
    def _make_request(command):
        command_class = type(command)
        kwargs = {SimulatorContext.request_command_map[command_class]: command}
        return pb2.TimelineSimulatorRequest(**kwargs)

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
            return next(self._responses)
        except (StopIteration, grpc.RpcError):
            self._responses = None
            raise

    def _assert_context_alive(self):
        if self._responses is None:
            raise RuntimeError("Edit context is dead. Create a new context.")

    def _start_simulator(self, timeline_id):
        response = self._send_command(pb2.TimelineSimulatorRequest.Start(timeline_id=timeline_id))
        return self._extract_response(response)

    def save_state_to_point(self):
        response = self._send_command(pb2.TimelineSimulatorRequest.SaveStateToPoint())
        return self._extract_response(response)

    def move_to_tick(self, tick: int):
        response = self._send_command(pb2.TimelineSimulatorRequest.MoveToTick(tick=tick))
        return self._extract_response(response)


class _CreatorContext:
    request_command_map = {
        pb2.TimelineCreatorRequest.StartNew: 'start_new',
        pb2.TimelineCreatorRequest.StartExisting: 'start_existing',
        pb2.TimelineCreatorRequest.StartEditing: 'start_editing',
        pb2.TimelineCreatorRequest.StopEditing: 'stop_editing',
        pb2.TimelineCreatorRequest.LoadState: 'load_state',
        pb2.TimelineCreatorRequest.SaveToNewTimeline: 'save_to_new_timeline',
    }

    def __init__(self, stub: pb2_grpc.SimmaStub):
        self._stub = stub

        self._command_queue = Queue(maxsize=1)

        self._responses = self._stub.TimelineCreator(self._request_provider())

    @staticmethod
    def _make_request(command):
        command_class = type(command)
        kwargs = {_CreatorContext.request_command_map[command_class]: command}
        return pb2.TimelineSimulatorRequest(**kwargs)

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
            return next(self._responses)
        except (StopIteration, grpc.RpcError):
            self._responses = None
            raise

    def _assert_context_alive(self):
        if self._responses is None:
            raise RuntimeError("Edit context is dead. Create a new context.")

    def start_editing(self):
        response = self._send_command(pb2.TimelineCreatorRequest.StartEditing())
        return self._extract_response(response)

    def stop_editing(self):
        response = self._send_command(pb2.TimelineCreatorResponse.StopEditing())
        return self._extract_response(response)

    def load_state(self, timeline_id):
        response = self._send_command(pb2.TimelineCreatorResponse.LoadState(timeline_id=timeline_id))
        return self._extract_response(response)

    def save_state_to_new_timeline(self):
        response = self._send_command(pb2.TimelineCreatorResponse.SaveToNewTimeline())
        return self._extract_response(response)


class NewCreatorContext(_CreatorContext):
    def __init__(self, stub: pb2_grpc.SimmaStub, binary_id, initial_timeline_id, tick):
        super().__init__(stub)
        success, response = self._start_new_creator(binary_id, initial_timeline_id, tick)
        if not success:
            raise RuntimeError("Failed to start simulator")
        self.creator_id = response.creator_id
        self.address = response.address
        self.user_token = response.user_token

    def _start_new_creator(self, binary_id, initial_timeline_id, tick):
        response = self._send_command(pb2.TimelineCreatorRequest.StartNew(binary_id=binary_id,
                                                                          initial_timeline_id=initial_timeline_id,
                                                                          tick=tick))
        return self._extract_response(response)


class ExistingCreatorContext(_CreatorContext):
    def __init__(self, stub: pb2_grpc.SimmaStub, creator_id):
        super().__init__(stub)
        success, response = self._start_existing_creator(creator_id)
        if not success:
            raise RuntimeError("Failed to start simulator")
        self.address = response.address
        self.user_token = response.user_token

    def _start_existing_creator(self, creator_id):
        response = self._send_command(pb2.TimelineCreatorRequest.StartExisting(creator_id=creator_id))
        return self._extract_response(response)


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
        request.filter_parent_ids[:] = filter_parents
        request.require_tags[:] = require_tags
        request.disallow_tags[:] = disallow_tags

        response = self._stub.GetTimelines(request)
        return list(response.timeline_ids)

    def get_timeline_ticks(self, timeline_id):
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

    def get_timeline_details(self, timeline_id: list[int]):
        request = pb2.GetTimelineDetailsRequest(timeline_id=timeline_id)
        response = self._stub.GetTimelineDetails(request)

        return TimelineDetails(binary_id=response.binary_id,
                               parent_id=response.parent_id,
                               head_tick=response.head_tick,
                               creation_timestamp=response.creation_timestamp,
                               tags=tuple(response.tags))
