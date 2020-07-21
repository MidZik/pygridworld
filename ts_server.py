import grpc
from concurrent import futures

import SimulationManager as sm
import TimelinesService_pb2 as ts
import TimelinesService_pb2_grpc as ts_grpc


class Service(ts_grpc.TimelineServiceServicer):
    def __init__(self, project: sm.TimelinesProject):
        self._project = project

    def GetTimelineTicks(self, request, context):
        try:
            node = self._project.get_timeline_node(request.timeline_id)
            message = ts.TimelineTicksResponse()
            message.ticks[:] = node.timeline.tick_list
            return message
        except LookupError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Timeline ID not found.')
            raise ValueError('Timeline ID not found.')

    def GetTimelineData(self, request, context):
        timeline_id = request.timeline_id
        tick = request.tick

        try:
            node = self._project.get_timeline_node(timeline_id)
        except LookupError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Timeline ID not found.')
            raise ValueError('Timeline ID not found.')

        try:
            point = node.point(tick)
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('tick not found.')
            raise ValueError('tick not found.')

        with point.point_file_path().open('rb') as point_file:
            return ts.TimelineDataResponse(data=point_file.read())


class Server:
    def __init__(self, project_to_serve, address='[::]:4969'):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
        self.server = server
        ts_grpc.add_TimelineServiceServicer_to_server(Service(project_to_serve), server)
        server.add_insecure_port(address)

    def start(self):
        self.server.start()

    def stop(self, grace=None):
        self.server.stop(grace)

    def __del__(self):
        self.stop()
