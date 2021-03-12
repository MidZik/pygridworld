import grpc

import TimelinesService_pb2 as ts
import TimelinesService_pb2_grpc as ts_grpc
from collections import namedtuple
from queue import Queue


Event = namedtuple('Event', 'name json')
Command = ts.EditSimulationRequest.Command
RpcError = grpc.RpcError
StatusCode = grpc.StatusCode


class EditorContext:
    def __init__(self, channel, timeline_id, token):
        self._stub = ts_grpc.TimelineServiceStub(channel)
        self._metadata = (('x-user-token', token),)
        self._timeline_id = timeline_id

        self._command_queue = Queue(maxsize=1)

        self._responses = self._stub.EditSimulation(self._request_provider(), metadata=self._metadata)

        self._start_editing()

    def _request_provider(self):
        command = self._command_queue.get()
        while command is not None:
            yield ts.EditSimulationRequest(timeline_id=self._timeline_id, command=command)
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

    def _start_editing(self):
        response = self._send_command(Command.START)
        return response.success, response.result

    def end_editing(self):
        response = self._send_command(Command.END)
        self._command_queue.put(None)
        self._command_queue.join()
        self._responses = None
        return response.success, response.result

    def discard_edits(self):
        response = self._send_command(Command.DISCARD)
        return response.success, response.result

    def commit_edits(self):
        response = self._send_command(Command.COMMIT)
        return response.success, response.result


class Client:
    def __init__(self, address):
        self._address = address
        self._channel = None

    def open(self):
        self._channel = grpc.insecure_channel(self._address)
        grpc.channel_ready_future(self._channel).result()

    def close(self):
        self._channel.close()
        self._channel = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_timelines(self, *, parent_id=None, head_tick=None, tags=None, exclude_tags=None):
        stub = ts_grpc.TimelineServiceStub(self._channel)

        if parent_id is None:
            parent_id = -1

        if tags is None:
            tags = ()

        if head_tick is None:
            head_tick = -1

        if exclude_tags is None:
            exclude_tags = ()

        request = ts.TimelinesRequest()
        request.tags[:] = tags
        request.parent_id = parent_id
        request.head_tick = head_tick
        request.exclude_tags[:] = exclude_tags

        response = stub.GetTimelines(request)
        return list(response.timeline_ids)

    def get_timeline_ticks(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        response = stub.GetTimelineTicks(ts.TimelineTicksRequest(timeline_id=timeline_id))
        return list(response.tick_list.ticks)

    def get_timeline_data(self, timeline_id, *, ticks=None, start_tick=None, end_tick=None):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = None
        if ticks is not None:
            tick_list = ts.TickList(ticks=ticks)
            request = ts.TimelineDataRequest(timeline_id=timeline_id, tick_list=tick_list)
        elif start_tick is not None:
            tick_range = ts.TickRange(start_tick=start_tick, end_tick=end_tick)
            request = ts.TimelineDataRequest(timeline_id=timeline_id, tick_range=tick_range)
        responses = stub.GetTimelineData(request)
        for response in responses:
            yield response.tick, response.data

    def get_timeline_json(self, timeline_id, *, ticks=None, start_tick=None, end_tick=None):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = None
        if ticks is not None:
            tick_list = ts.TickList(ticks=ticks)
            request = ts.TimelineJsonRequest(timeline_id=timeline_id, tick_list=tick_list)
        elif start_tick is not None:
            if end_tick is None:
                end_tick = -1
            tick_range = ts.TickRange(start_tick=start_tick, end_tick=end_tick)
            request = ts.TimelineJsonRequest(timeline_id=timeline_id, tick_range=tick_range)
        else:
            raise ValueError("Parameters incorrect.")
        responses = stub.GetTimelineJson(request)
        for response in responses:
            yield response.tick, response.json

    def get_timeline_events(self, timeline_id, *, start_tick=0, end_tick=-1, filters=None):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        tick_range = ts.TickRange(start_tick=start_tick, end_tick=end_tick)
        request = ts.TimelineEventsRequest(timeline_id=timeline_id, tick_range=tick_range)
        if filters is not None:
            request.filters[:] = filters

        responses = stub.GetTimelineEvents(request)
        for response in responses:
            tick = response.tick
            events = []
            for e in response.events:
                events.append(Event(e.name, e.json))

            yield tick, events

    def get_or_start_simulation(self, timeline_id, tick=None):
        stub = ts_grpc.TimelineServiceStub(self._channel)

        if tick is None:
            tick = -1

        request = ts.GetOrStartSimulationRequest(timeline_id=timeline_id, tick=tick)

        response = stub.GetOrStartSimulation(request)
        return response.address, response.token

    def stop_simulation(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.StopSimulationRequest(timeline_id=timeline_id)
        stub.StopSimulation(request)

    def move_to_tick(self, timeline_id, tick):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.MoveSimToTickRequest(timeline_id=timeline_id, tick=tick)
        stub.MoveSimToTick(request)

    def start_editing(self, timeline_id, token):
        return EditorContext(self._channel, timeline_id, token)

    def get_timeline_tags(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.GetTimelineTagsRequest(timeline_id=timeline_id)
        response = stub.GetTimelineTags(request)
        return list(response.tags)

    def modify_timeline_tags(self, timeline_id, *, tags_to_add=(), tags_to_remove=()):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.ModifyTimelineTagsRequest(timeline_id=timeline_id)
        request.tags_to_add[:] = tags_to_add
        request.tags_to_remove[:] = tags_to_remove
        stub.ModifyTimelineTags(request)

    def create_timeline(self, source_timeline_id=None, source_tick=None):
        stub = ts_grpc.TimelineServiceStub(self._channel)

        if source_timeline_id is not None and source_tick is None:
            raise ValueError("source_tick must be provided if source_timeline_id is provided.")

        if source_timeline_id is None:
            source_timeline_id = 0
            source_tick = -1

        request = ts.CreateTimelineRequest(source_timeline_id=source_timeline_id, source_tick=source_tick)
        response = stub.CreateTimeline(request)
        return response.created_timeline_id

    def clone_timeline(self, source_timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.CreateTimelineRequest(source_timeline_id=source_timeline_id)
        response = stub.CloneTimeline(request)
        return response.created_timeline_id

    def create_timeline_from_simulation(self, source_timeline_id, as_sibling=False):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.CreateTimelineFromSimulationRequest(source_timeline_id=source_timeline_id, as_sibling=as_sibling)
        response = stub.CreateTimelineFromSimulation(request)
        return response.created_timeline_id

    def get_timeline_last_commit_info(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.GetTimelineLastCommitInfoRequest(timeline_id=timeline_id)
        response = stub.GetTimelineLastCommitInfo(request)
        return response.timestamp,

    def delete_timeline(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.DeleteTimelineRequest(timeline_id=timeline_id)
        stub.DeleteTimeline(request)
