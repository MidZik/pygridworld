import asyncio
import grpc
import logging
from typing import AsyncIterable
from uuid import UUID

from simma.service import ProjectService, Project
import simma.simma_pb2 as pb2
import simma.simma_pb2_grpc as pb2_grpc


_logger = logging.getLogger(__name__)


class Service(pb2_grpc.SimmaServicer):
    def __init__(self, project_service: ProjectService):
        self._service = project_service
    
    async def GetTimelines(self, request: pb2.TimelinesRequest, context):
        _logger.debug(request)
        filter_parent_ids = (UUID(item) if item else None for item in request.filter_parent_ids)
        require_tags = {tag for tag in request.require_tags}
        disallow_tags = {tag for tag in request.disallow_tags}

        found_timelines = await self._service.find_timelines(filter_parent_ids, require_tags, disallow_tags)

        response = pb2.TimelinesResponse()
        response.timeline_ids[:] = [info.timeline_id for info in found_timelines]
        _logger.debug(response)
        return response

    async def GetTimelineTicks(self, request: pb2.TimelineTicksRequest, context):
        timeline_id = UUID(request.timeline_id)

        points = await self._service.get_timeline_points(timeline_id)

        response = pb2.TimelineTicksResponse()
        response.tick_list.ticks[:] = (tick for tick, _ in points)
        return response

    async def GetTimelineData(self, request: pb2.TimelineDataRequest, context):
        timeline_id = UUID(request.timeline_id)
        tick_option = request.WhichOneof('tick_option')

        if tick_option == 'tick_list':
            for tick in request.tick_list.ticks:
                point_path = await self._service.get_timeline_point(timeline_id, tick)
                if point_path is None:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details(f'tick {tick} not found.')
                    raise ValueError(f'tick {tick} not found.')
                else:
                    data = await asyncio.to_thread(point_path.read_bytes)
                    yield pb2.TimelineDataResponse(tick=tick, data=data)
        elif tick_option == 'tick_range':
            start_tick = request.tick_range.start_tick
            end_tick = request.tick_range.end_tick
            points = ((tick, point_path)
                      for tick, point_path
                      in await self._service.get_timeline_points(timeline_id)
                      if start_tick <= tick <= end_tick)
            for tick, point_path in points:
                data = await asyncio.to_thread(point_path.read_bytes)
                yield pb2.TimelineDataResponse(tick=tick, data=data)

    async def GetTimelineJson(self, request: pb2.TimelineJsonRequest, context):
        timeline_id = UUID(request.timeline_id)
        tick_option = request.WhichOneof('tick_option')

        async with self._service.timeline_point_json_generator() as json_generator:
            if tick_option == 'tick_list':
                for tick in request.tick_list.ticks:
                    point_path = await self._service.get_timeline_point(timeline_id, tick)
                    if point_path is None:
                        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                        context.set_details(f'tick {tick} not found.')
                        raise ValueError(f'tick {tick} not found.')
                    else:
                        json = await json_generator.asend(str(point_path))
                        yield pb2.TimelineJsonResponse(tick=tick, json=json)
            elif tick_option == 'tick_range':
                start_tick = request.tick_range.start_tick
                end_tick = request.tick_range.end_tick
                points = ((tick, point_path)
                          for tick, point_path
                          in await self._service.get_timeline_points(timeline_id)
                          if start_tick <= tick <= end_tick)
                for tick, point_path in points:
                    json = await json_generator.asend(str(point_path))
                    yield pb2.TimelineJsonResponse(tick=tick, json=json)

    async def GetTimelineEvents(self, request: pb2.TimelineEventsRequest, context):
        timeline_id = UUID(request.timeline_id)
        start_tick = request.tick_range.start_tick
        end_tick = request.tick_range.end_tick
        if end_tick == -1:
            end_tick = None
        event_name_filters = list(request.event_name_filters)

        events = self._service.get_timeline_events(timeline_id,
                                                   start_tick=start_tick,
                                                   end_tick=end_tick,
                                                   event_name_filters=event_name_filters)

        cur_response = None
        for tick, name, json in events:
            if cur_response is None or cur_response.tick != tick:
                if cur_response is not None:
                    yield cur_response
                cur_response = pb2.TimelineEventsResponse(timeline_id=timeline_id, tick=tick)
            cur_response.events.append(pb2.EventMessage(name=name, json=json))

        if cur_response is not None:
            yield cur_response

    async def TimelineSimulator(self, request_iterable: AsyncIterable[pb2.TimelineSimulatorRequest], context):
        iterator = aiter(request_iterable)
        first_request = await anext(iterator)
        message = first_request.WhichOneof('message')
        if message != 'start':
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            raise RuntimeError("First message must be 'start'.")
        start_request = first_request.start
        timeline_id = UUID(start_request.timeline_id)

        async with self._service.timeline_simulator(timeline_id) as simulator:
            start_response = pb2.TimelineSimulatorResponse.Start(
                address=simulator.get_process_address(), user_token=simulator.user_token)
            yield pb2.TimelineSimulatorResponse(start=start_response)
            async for request in iterator:
                message = request.WhichOneof('message')
                if message == 'save_state_to_point':
                    new_tick = await simulator.save_state_to_new_point()
                    if new_tick is None:
                        new_tick = -1
                    sstp_response = pb2.TimelineSimulatorResponse.SaveStateToPoint(new_tick=new_tick)
                    yield pb2.TimelineSimulatorResponse(save_state_to_point=sstp_response)
                elif message == 'move_to_tick':
                    tick = request.move_to_tick.tick
                    await simulator.move_to_tick(tick)
                    yield pb2.TimelineSimulatorResponse(move_to_tick=pb2.TimelineSimulatorResponse.MoveToTick())
                else:
                    yield pb2.TimelineSimulatorResponse(
                        error=pb2.TimelineSimulatorResponse.Error(message="Unexpected simulator request message."))

    async def TimelineCreator(self, request_iterable: AsyncIterable[pb2.TimelineCreatorRequest], context):
        iterator = aiter(request_iterable)
        first_request = await anext(iterator)
        message = first_request.WhichOneof('message')
        if message == 'start_new':
            start_new_request = first_request.start_new
            binary_id = UUID(start_new_request.binary_id)
            initial_timeline_id = UUID(start_new_request.initial_timeline_id)
            tick = start_new_request.tick
            context_manager = self._service.new_timeline_creator(binary_id, initial_timeline_id, tick)
        elif message == 'start_existing':
            start_existing_request = first_request.start_existing
            creator_id = UUID(start_existing_request.creator_id)
            context_manager = self._service.existing_timeline_creator(creator_id)
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            raise RuntimeError("First message must be 'start_new' or 'start_existing'.")

        async with context_manager as result:
            if message == 'start_new':
                creator_id, creator = result
                start_new_response = pb2.TimelineCreatorResponse.StartNew(
                    creator_id=creator_id, address=creator.get_process_address(), user_token=creator.user_token)
                yield pb2.TimelineCreatorResponse(start_new=start_new_response)
            elif message == 'start_existing':
                creator = result
                start_existing_response = pb2.TimelineCreatorResponse.StartExisting(
                    address=creator.get_process_address(), user_token=creator.user_token)
                yield pb2.TimelineCreatorResponse(start_existing=start_existing_response)
            async for request in iterator:
                message = request.WhichOneof('message')
                if message == 'start_editing':
                    with creator.editor(creator.user_token) as editor:
                        yield pb2.TimelineCreatorResponse(start_editing=pb2.TimelineCreatorResponse.StartEditing())
                        async for editor_request in iterator:
                            message = editor_request.WhichOneof('message')
                            if message == 'stop_editing':
                                break
                            elif message == 'load_state':
                                load_timeline_id = editor_request.timeline_id
                                await editor.load_state(load_timeline_id)
                                yield pb2.TimelineCreatorResponse(load_state=pb2.TimelineCreatorResponse.LoadState())
                            elif message == 'save_to_new_timeline':
                                new_timeline_id = await editor.save_state_as_new_timeline()
                                save_to_new_timeline_response = pb2.TimelineCreatorResponse.SaveToNewTimeline(
                                    new_timeline_id=new_timeline_id)
                                yield pb2.TimelineCreatorResponse(save_to_new_timeline=save_to_new_timeline_response)
                            else:
                                yield pb2.TimelineCreatorResponse(
                                    error=pb2.TimelineCreatorResponse.Error(
                                        message="Unexpected creator request message."))
                        yield pb2.TimelineCreatorResponse(stop_editing=pb2.TimelineCreatorResponse.StopEditing())
                else:
                    yield pb2.TimelineCreatorResponse(
                        error=pb2.TimelineCreatorResponse.Error(message="Unexpected creator request message."))

    async def ModifyTimelineTags(self, request: pb2.ModifyTimelineTagsRequest, context):
        timeline_id = UUID(request.timeline_id)
        tags_to_add = set(request.tags_to_add)
        tags_to_remove = set(request.tags_to_remove)

        await self._service.modify_timeline_tags(timeline_id, tags_to_add=tags_to_add, tags_to_remove=tags_to_remove)

        return pb2.ModifyTimelineTagsResponse()

    async def DeleteTimeline(self, request: pb2.DeleteTimelineRequest, context):
        timeline_id = UUID(request.timeline_id)

        await self._service.delete_timeline(timeline_id)

        return pb2.DeleteTimelineResponse()

    async def GetTimelineDetails(self, request: pb2.GetTimelineDetailsRequest, context):
        timeline_id = UUID(request.timeline_id)

        timeline_info = await self._service.get_timeline(timeline_id)
        timeline_tags = await self._service.get_timeline_tags(timeline_id)

        return pb2.GetTimelineDetailsResponse(binary_id=str(timeline_info.binary_id),
                                              parent_id=str(timeline_info.parent_id) if timeline_info.parent_id else "",
                                              head_tick=timeline_info.head_tick,
                                              creation_timestamp=str(timeline_info.creation_time),
                                              tags=timeline_tags)


def make_server(project_service: ProjectService, address='[::]:4969'):
    server = grpc.aio.server()
    pb2_grpc.add_SimmaServicer_to_server(Service(project_service), server)
    server.add_insecure_port(address)
    return server


async def serve():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Run a simma project server.")
    parser.add_argument('--create', action='store_true',
                        help="If provided, create a project instead of running the server.")
    parser.add_argument('project_path', type=Path, nargs='?', default=Path.cwd(),
                        help="If provided, the path to the project to server or create. "
                             "If not provided, uses current working directory.")

    args = parser.parse_args()
    project_path = args.project_path.resolve()

    if args.create:
        await Project.create(project_path)
    else:
        project_service = ProjectService(project_path)
        server = make_server(project_service)
        print(f"Starting server with project {project_path}")
        await server.start()

        async def graceful_shutdown():
            _logger.info("Server shutting down gracefully...")
            await server.stop(5)
            _logger.info("Graceful server shutdown complete.")

        _cleanup_coroutines.append(graceful_shutdown())
        await server.wait_for_termination()

_cleanup_coroutines = []
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(serve())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
