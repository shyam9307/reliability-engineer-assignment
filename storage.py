import json
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).with_name("pipeline.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        # Store successfully processed events.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS processed_events (
                event_id TEXT PRIMARY KEY,
                audio_ref TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Store events that fail after all retry attempts.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS dead_letters (
                event_id TEXT PRIMARY KEY,
                audio_ref TEXT NOT NULL,
                reason TEXT NOT NULL,
                replay_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_attempt_at TEXT
            )
        """)


def get_processed_event(event_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT event_id, audio_ref, response_json
            FROM processed_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "event_id": row["event_id"],
        "audio_ref": row["audio_ref"],
        "response": json.loads(row["response_json"]),
    }


def save_processed_event(event_id, audio_ref, response):
    response_json = json.dumps(response)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO processed_events (
                event_id, audio_ref, response_json
            )
            VALUES (?, ?, ?)
            """,
            (event_id, audio_ref, response_json),
        )


def save_dead_letter(event_id, audio_ref, reason):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO dead_letters (event_id, audio_ref, reason)
            VALUES (?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                reason = excluded.reason,
                last_attempt_at = CURRENT_TIMESTAMP
            """,
            (event_id, audio_ref, reason),
        )


def get_dead_letter(event_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT event_id, audio_ref, reason, replay_count,
                   created_at, last_attempt_at
            FROM dead_letters
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def list_dead_letters():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_id, audio_ref, reason, replay_count,
                   created_at, last_attempt_at
            FROM dead_letters
            ORDER BY created_at
            """
        ).fetchall()

    return [dict(row) for row in rows]


def increment_dead_letter_replay_count(event_id):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE dead_letters
            SET replay_count = replay_count + 1,
                last_attempt_at = CURRENT_TIMESTAMP
            WHERE event_id = ?
            """,
            (event_id,),
        )


def delete_dead_letter(event_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM dead_letters WHERE event_id = ?",
            (event_id,),
        )