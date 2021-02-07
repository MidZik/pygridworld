import grpc
from concurrent import futures

import SimulationManager as sm
import simrunner as sr
import TimelinesService_pb2 as ts
import TimelinesService_pb2_grpc as ts_grpc

import traceback

Command = ts.EditSimulationRequest.Command


class Service(ts_grpc.TimelineServiceServicer):
    def __init__(self, project: sm.TimelinesProject):
        self._project = project

    def GetTimelines(self, request, context):
        nodes = self._project.get_all_timeline_nodes()
        message = ts.TimelinesResponse()
        message.timeline_ids[:] = [node.timeline_id for node in nodes if node.timeline_id is not None]
        return message

    def GetTimelineTicks(self, request, context):
        try:
            node = self._project.get_timeline_node(request.timeline_id)
            message = ts.TimelineTicksResponse()
            message.tick_list.ticks[:] = node.timeline.tick_list
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

    def GetTimelineEvents(self, request, context):
        timeline_id = request.timeline_id

        try:
            node = self._project.get_timeline_node(timeline_id)
        except LookupError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Timeline ID not found.')
            raise ValueError('Timeline ID not found.')

        start_tick = request.tick_range.start_tick
        end_tick = request.tick_range.end_tick
        if end_tick == -1:
            end_tick = None

        events = self._project.get_timeline_events(timeline_id,
                                                   start_tick=start_tick,
                                                   end_tick=end_tick,
                                                   filters=request.filters)

        cur_response = None
        for (tick, name, json) in events:
            if cur_response is None or cur_response.tick != tick:
                if cur_response is not None:
                    yield cur_response
                cur_response = ts.TimelineEventsResponse(timeline_id=timeline_id, tick=tick)
            cur_response.events.append(ts.EventMessage(name=name, json=json))

        if cur_response is not None:
            yield cur_response

    def GetOrStartSimulation(self, request, context):
        timeline_id = request.timeline_id
        tick = request.tick

        if tick == -1:
            start_spec = timeline_id
        else:
            start_spec = self._project.get_timeline_node(timeline_id).point(tick)

        sim = self._project.get_or_start_simulation(start_spec)
        address, token = sim.make_connection_parameters()

        return ts.GetOrStartSimulationResponse(address=address, token=token)

    def StopSimulation(self, request, context):
        timeline_id = request.timeline_id

        self._project.stop_simulation(timeline_id)

        return ts.StopSimulationResponse()

    def MoveSimToTick(self, request, context):
        timeline_id = request.timeline_id
        tick = request.tick

        timeline_sim = self._project.get_simulation(timeline_id)
        if timeline_sim is None:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            raise RuntimeError("Simulation is not running.")

        if tick == -1:
            tick = timeline_sim.timeline.head()

        timeline_sim.move_to_tick(tick)

        return ts.MoveSimToTickResponse()

    def EditSimulation(self, request_iterator, context):
        first_request = next(request_iterator)

        timeline_id = first_request.timeline_id
        command = first_request.command
        metadata = {k: v for k, v in context.invocation_metadata()}
        token = metadata['x-user-token']

        if command != Command.START:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            raise RuntimeError("First edit command must be START.")

        timeline_sim = self._project.get_simulation(timeline_id)

        if timeline_sim is None:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            raise RuntimeError("Simulation is not running.")

        try:
            with timeline_sim.editor(token):
                yield ts.EditSimulationResponse(success=True)

                for request in request_iterator:
                    command = request.command

                    if command == Command.START:
                        yield ts.EditSimulationResponse(success=False, result="Editing already started.")
                    elif command == Command.END:
                        break
                    elif command == Command.DISCARD:
                        timeline_sim.discard_edits(token)
                        yield ts.EditSimulationResponse(success=True)
                    elif command == Command.COMMIT:
                        timeline_sim.commit_edits(token)
                        yield ts.EditSimulationResponse(success=True)
                    else:
                        yield ts.EditSimulationResponse(success=False, result=f"Unknown command: {command}")
        except grpc.RpcError as e:
            if not context.is_active():
                # the editing has been cancelled
                return
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Editing ended due to exception.\n" + str(e))
            traceback.print_exc()
            raise
        else:
            yield ts.EditSimulationResponse(success=True, result="Editing ended.")


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
