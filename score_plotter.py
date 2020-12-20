import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict
import sqlite3
import argparse


def _show_figure(db, time_between_refresh):
    fig, ax = plt.subplots(num=f"Scores")
    ax.set_title('Scores')

    def update(frame):
        ax.clear()

        with sqlite3.Connection(db) as conn:
            c = conn.execute('SELECT timeline_id, tick, score '
                             'FROM scores '
                             'ORDER BY timeline_id ASC, tick ASC')

            row = c.fetchone()

            cur_id = None
            cur_x = []
            cur_y = []

            while row is not None:
                timeline_id, tick, score = row
                if cur_id != timeline_id:
                    if cur_id is not None:
                        ax.plot(cur_x, cur_y, label=cur_id)
                        ax.legend()
                    cur_id = timeline_id
                    cur_x = []
                    cur_y = []
                cur_x.append(tick)
                cur_y.append(score)
                row = c.fetchone()

            ax.plot(cur_x, cur_y, label=cur_id)
            ax.legend()

        ax.relim()
        ax.autoscale_view()

    ani = animation.FuncAnimation(fig, update, interval=time_between_refresh * 1000)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser('Create a score plot')
    parser.add_argument('db_path', type=str)
    parser.add_argument('time_between_refresh', type=int)
    args = parser.parse_args()
    _show_figure(args.db_path, args.time_between_refresh)
