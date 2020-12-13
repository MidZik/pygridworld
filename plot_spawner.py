import subprocess
from pathlib import Path

_root = Path(__file__).parent


class PlotSpawner:
    def __init__(self, db):
        self.db = db

    def pop_plot(self, timeline_id, min_pop_length_to_plot=4, time_between_refresh=10):
        subprocess.Popen([
            'python',
            str(_root / 'pop_plotter.py'),
            str(self.db),
            str(timeline_id),
            str(min_pop_length_to_plot),
            str(time_between_refresh)
        ])

    def score_plot(self, time_between_refresh=10):
        subprocess.Popen([
            'python',
            str(_root / 'score_plotter.py'),
            str(self.db),
            str(time_between_refresh)
        ])
