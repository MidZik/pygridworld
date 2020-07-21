import grpc

import TimelinesService_pb2 as ts
import TimelinesService_pb2_grpc as ts_grpc

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

    def get_timeline_ticks(self, timeline_id):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        response = stub.GetTimelineTicks(ts.TimelineTicksRequest(timeline_id=timeline_id))
        return response.ticks

    def get_timeline_data(self, timeline_id, tick):
        stub = ts_grpc.TimelineServiceStub(self._channel)
        request = ts.TimelineDataRequest(timeline_id=timeline_id, tick=tick)
        response = stub.GetTimelineData(request)
        return response.data
