import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict
import sqlite3
import argparse
import subprocess


def create_populations_figure(db, timeline_id, min_pop_length_to_plot=4, time_between_refresh=10):
    subprocess.Popen(['python', __file__, str(db), str(timeline_id), str(min_pop_length_to_plot), str(time_between_refresh)])


def _show_figure(db, timeline_id, min_pop_length_to_plot, time_between_refresh):
    fig, ax = plt.subplots(num=f"Populations for {timeline_id}")
    ax.clear()
    ax.set_title(f"Populations for {timeline_id}")

    population_data = defaultdict(lambda: ([], []))
    plots = defaultdict(lambda: ax.plot([], [])[0])

    last_tick = -1

    def update(frame):
        nonlocal last_tick
        with sqlite3.Connection(db) as conn:
            c = conn.execute('SELECT tick, major_name, count '
                             'FROM populations '
                             'WHERE timeline_id = ? AND tick > ?'
                             'ORDER BY timeline_id ASC, tick ASC'
                             , [timeline_id, last_tick])

            row = c.fetchone()

            while row is not None:
                tick, major_name, count = row
                ticks, counts = population_data[major_name]
                ticks.append(tick)
                counts.append(count)

                last_tick = tick

                row = c.fetchone()

            for major_name, (ticks, counts) in population_data.items():
                if len(ticks) >= min_pop_length_to_plot:
                    plot: plt.Line2D = plots[major_name]
                    plot.set_data(ticks, counts)

            ax.relim()
            ax.autoscale_view()

    ani = animation.FuncAnimation(fig, update, interval=time_between_refresh * 1000)
    plt.show(block=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser('Create a population plot')
    parser.add_argument('db_path', type=str)
    parser.add_argument('timeline_id', type=int)
    parser.add_argument('min_pop_length', type=int)
    parser.add_argument('time_between_refresh', type=int)
    args = parser.parse_args()
    _show_figure(args.db_path, args.timeline_id, args.min_pop_length, args.time_between_refresh)
