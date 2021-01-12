import grpc

import TimelinesService_pb2 as ts
import TimelinesService_pb2_grpc as ts_grpc
from collections import namedtuple


Event = namedtuple('Event', 'name json')


class Client:
    def __init__(self, address):
        self._address = address
        self._channel = None

    def open(self):
        self._channel = grpc.insecure_channel(self._address)

    def close(self):
        self._channel.close()
        self._channel = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_timelines(self):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        response = stub.GetTimelines(ts.TimelinesRequest())
        return response.timeline_ids

    def get_timeline_ticks(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        response = stub.GetTimelineTicks(ts.TimelineTicksRequest(timeline_id=timeline_id))
        return response.tick_list.ticks

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
