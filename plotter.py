import matplotlib.pyplot as plt
from collections import defaultdict
import json
from multiprocessing.connection import Client


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
    con = Client((server, port), authkey=b'local-timelines-project-server')
    con.send(("get_ticks", (timeline_id,)))
    result, ticks = con.recv()
    if not result:
        raise RuntimeError()

    pop_plotter = PopulationsFigure(timeline_id)

    for tick in ticks:
        con.send(("get_state", (timeline_id, tick)))
        result, state = con.recv()
        pop_plotter.add_json_data(state)

    return pop_plotter
