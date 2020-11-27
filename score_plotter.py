import matplotlib.pyplot as plt
import sqlite3


def create_scores_figure(db):
    with sqlite3.Connection(db) as conn:
        fig, ax = plt.subplots(num=f"Scores")
        ax.clear()
        ax.set_title('Scores')

        cur_id = None
        cur_x = []
        cur_y = []

        c = conn.cursor()

        c.execute('SELECT timeline_id, tick, score FROM scores ORDER BY timeline_id ASC, tick ASC')

        row = c.fetchone()

        while row is not None:
            timeline_id, tick, score = row
            if cur_id != timeline_id:
                if cur_id is not None:
                    ax.plot(cur_x, cur_y, label=cur_id)
                cur_id = timeline_id
                cur_x = []
                cur_y = []
            cur_x.append(tick)
            cur_y.append(score)
            row = c.fetchone()

        ax.relim()
        ax.autoscale_view()
