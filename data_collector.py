import sqlite3
import json
import ts_client


class EvoEventScoreProcessor:
    @staticmethod
    def prepare_db(db_conn: sqlite3.Connection):
        cursor = db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                timeline_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                score REAL,
                PRIMARY KEY(timeline_id, tick)
            )''')
        cursor.close()

    @staticmethod
    def process_state(db_conn: sqlite3.Connection, timeline_id, tick, events):
        cursor = db_conn.cursor()
        try:
            evo_data = events.get('sim.evolution')

            if evo_data is None:
                return

            scores = []
            for log in evo_data["scored_entities"].values():
                scores.append(log["score"])

            if len(scores) < 6:
                print(f"[{timeline_id}, {tick}] sim.evolution event has less than 6 scored entities; skipping")
                return

            state_score = sum(sorted(scores, reverse=True)[:6]) / 6

            cursor.execute('INSERT OR REPLACE INTO scores (timeline_id, tick, score) VALUES (?, ?, ?)',
                           (timeline_id, tick, state_score))
        finally:
            cursor.close()


processors = [
    EvoEventScoreProcessor
]


def one_time_collection(db_file, server_address='127.0.0.1:4969'):
    db_conn = sqlite3.connect(db_file)

    for p in processors:
        p.prepare_db(db_conn)

    with ts_client.Client(server_address) as client:
        timeline_ids = client.get_timelines()

        for timeline_id in timeline_ids:
            for tick, events_list in client.get_timeline_events(timeline_id):
                events = {event.name: json.loads(event.json) for event in events_list}
                for p in processors:
                    p.process_state(db_conn, timeline_id, tick, events)

    db_conn.commit()
    db_conn.close()
