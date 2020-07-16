import matplotlib.pyplot as plt
from collections import defaultdict
import json
import grpc
import TimelinesService_pb2
import TimelinesService_pb2_grpc


class PopulationsFigure:
    def __init__(self, timeline_id):
        fig, ax = plt.subplots(num=f"Populations for {timeline_id}")
        self._fig = fig
        self._ax = ax

        self.min_pop_length_to_plot = 10
        self.population_data = defaultdict(lambda: ([], []))

        ax.clear()
        ax.set_title('Population')

        self.plots = defaultdict(lambda: ax.plot([], [])[0])

    def add_file(self, state_file_path):
        with state_file_path.open('r') as state_file:
            state = json.load(state_file)
            self.add_state_data(state)

    def add_json_data(self, json_data):
        self.add_state_data(json.loads(json_data))

    def add_state_data(self, state):
        tick = state["singletons"]["STickCounter"]
        populations = defaultdict(lambda: 0)

        for named_entity in state["components"]["Name"]:
            major_name = named_entity["Com"]["major_name"]
            populations[major_name] += 1

        for major_name, population in populations.items():
            ticks_data, population_data = self.population_data[major_name]
            ticks_data.append(tick)
            population_data.append(population)

            if len(ticks_data) > self.min_pop_length_to_plot:
                plot: plt.Line2D = self.plots[major_name]
                plot.set_data(ticks_data, population_data)

        self._ax.relim()
        self._ax.autoscale_view()


def make_pop_plotter(timeline_id, server='127.0.0.1', port=4969):
    with grpc.insecure_channel('localhost:4969') as channel:
        stub = TimelinesService_pb2_grpc.TimelineServiceStub(channel)
        response = stub.GetTimelineTicks(TimelinesService_pb2.TimelineTicksRequest(timeline_id=timeline_id))
        pop_plotter = PopulationsFigure(timeline_id)
        for tick in response.ticks:
            request = TimelinesService_pb2.TimelineDataRequest(timeline_id=timeline_id, tick=tick)
            state = stub.GetTimelineData(request).data
            pop_plotter.add_json_data(state)
