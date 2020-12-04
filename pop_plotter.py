import matplotlib.pyplot as plt
from collections import defaultdict
import sqlite3


def create_populations_figure(db, timeline_id, min_pop_length_to_plot=4):
    with sqlite3.Connection(db) as conn:
        fig, ax = plt.subplots(num=f"Populations for {timeline_id}")
        ax.clear()
        ax.set_title(f"Populations for {timeline_id}")

        population_data = defaultdict(lambda: ([], []))
        plots = defaultdict(lambda: ax.plot([], [])[0])

        c = conn.execute('SELECT tick, major_name, count '
                         'FROM populations '
                         'WHERE timeline_id = ? '
                         'ORDER BY timeline_id ASC, tick ASC'
                         , [timeline_id])

        row = c.fetchone()

        while row is not None:
            tick, major_name, count = row
            ticks, counts = population_data[major_name]
            ticks.append(tick)
            counts.append(count)

            row = c.fetchone()

        for major_name, (ticks, counts) in population_data.items():
            if len(ticks) >= min_pop_length_to_plot:
                plot: plt.Line2D = plots[major_name]
                plot.set_data(ticks, counts)

        ax.relim()
        ax.autoscale_view()
