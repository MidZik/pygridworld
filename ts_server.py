import grpc
from concurrent import futures

import SimulationManager as sm
import simrunner as sr
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
        tick_option = request.WhichOneof('tick_option')

        try:
            node = self._project.get_timeline_node(timeline_id)
        except LookupError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Timeline ID not found.')
            raise ValueError('Timeline ID not found.')

        if tick_option == 'tick_list':
            for tick in request.tick_list.ticks:
                try:
                    point = node.point(tick)
                except ValueError:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details(f'tick {tick} not found.')
                    raise ValueError(f'tick {tick} not found.')
                with point.point_file_path().open('rb') as point_file:
                    yield ts.TimelineDataResponse(tick=tick, data=point_file.read())
        elif tick_option == 'tick_range':
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details('tick_range option not implemented')
            raise NotImplementedError('tick_range option not implemented')

    def GetTimelineJson(self, request, context):
        timeline_id = request.timeline_id
        tick_option = request.WhichOneof('tick_option')

        try:
            node = self._project.get_timeline_node(timeline_id)
        except LookupError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Timeline ID not found.')
            raise ValueError('Timeline ID not found.')

        converter_generator = sr.SimulationProcess.convert_multiple_generator(
            "binary",
            str(node.timeline.get_simulation_binary_path()),
            "json")
        converter_generator.send(None)

        if tick_option == 'tick_list':
            for tick in request.tick_list.ticks:
                try:
                    point = node.point(tick)
                except ValueError:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details(f'tick {tick} not found.')
                    raise ValueError(f'tick {tick} not found.')
                json = converter_generator.send(str(point.point_file_path()))
                yield ts.TimelineJsonResponse(tick=tick, json=json)
        elif tick_option == 'tick_range':
            timeline = node.timeline
            start_tick = request.tick_range.start_tick
            end_tick = request.tick_range.end_tick

            for tick in timeline.tick_list:
                if tick < start_tick:
                    continue
                if end_tick != -1 and tick > end_tick:
                    break
                point = node.point(tick)
                json = converter_generator.send(str(point.point_file_path()))
                yield ts.TimelineJsonResponse(tick=tick, json=json)

        try:
            converter_generator.send(None)
        except StopIteration:
            pass


class Server:
    def __init__(self, project_to_serve, address='[::]:4969'):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
        self.server = server
        ts_grpc.add_TimelineServiceServicer_to_server(Service(project_to_serve), server)
        server.add_insecure_port(address)

    def start(self):
        self.server.start()

    def stop(self, grace=0):
        self.server.stop(grace)

    def __del__(self):
        self.stop()
