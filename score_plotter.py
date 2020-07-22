import matplotlib.pyplot as plt
from collections import defaultdict
import json
import ts_client


class ScoresFigure:
    def __init__(self, timeline_id):
        fig, ax = plt.subplots(num=f"Scores for {timeline_id}")
        self._fig = fig
        self._ax = ax

        self.ticks = []
        self.scores = []

        ax.clear()
        ax.set_title('Scores')

        self.plot = ax.plot([], [])[0]

    def add_file(self, state_file_path):
        with state_file_path.open('r') as state_file:
            state = json.load(state_file)
            self.add_state_data(state)

    def add_json_data(self, json_data):
        self.add_state_data(json.loads(json_data))

    def add_state_data(self, state):
        tick = state["singletons"]["STickCounter"]
        evo_data = next((e["data"] for e in state["singletons"]["SEventsLog"]["events_last_tick"]
                        if e["name"] == "evolution"), None)

        if evo_data is None:
            print("Provided state has no evolution data; skipping")
            return

        scores = []
        for log in evo_data["scored_entities"].values():
            scores.append(log["score"])

        if len(scores) < 6:
            print("Provided state has less than 6 scored entities; skipping")
            return

        state_score = sum(sorted(scores, reverse=True)[:6]) / 6

        self.ticks.append(tick)
        self.scores.append(state_score)

        self.plot.set_data(self.ticks, self.scores)

        self._ax.relim()
        self._ax.autoscale_view()


def make_score_plotter(timeline_id, address='127.0.0.1:4969'):
    with ts_client.Client(address) as client:
        ticks = client.get_timeline_ticks(timeline_id)
        pop_plotter = ScoresFigure(timeline_id)
        for tick in ticks:
            state = client.get_timeline_data(timeline_id, tick)
            pop_plotter.add_json_data(state)
