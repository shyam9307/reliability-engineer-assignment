import sqlite3

import storage


def test_processed_event_storage(tmp_path, monkeypatch):
    # Use a temporary database dedicated to this test.
    test_database = tmp_path / "test_pipeline.db"

    def get_test_connection():
        connection = sqlite3.connect(test_database, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    # Redirect storage operations to the temporary database.
    monkeypatch.setattr(storage, "get_connection", get_test_connection)

    # Create the database and its tables.
    storage.initialize_database()

    event_id = "storage-test-001"
    audio_ref = "synthetic"

    expected_response = {
        "status": "ok",
        "transcript": "synthetic transcript",
        "response_audio_ref": "synthetic",
        "latency_ms": 350,
    }

    # Save the event and its response.
    storage.save_processed_event(
        event_id,
        audio_ref,
        expected_response,
    )

    # Retrieve the saved event.
    saved_event = storage.get_processed_event(event_id)

    # Verify the saved values.
    assert saved_event is not None
    assert saved_event["event_id"] == event_id
    assert saved_event["audio_ref"] == audio_ref
    assert saved_event["response"] == expected_response

    # Retrieve it again using a new database connection.
    saved_event_again = storage.get_processed_event(event_id)
    assert saved_event_again == saved_event

    print("PASS: Database initialized successfully.")
    print("PASS: Event and response saved correctly.")
    print("PASS: Saved event retrieved successfully.")
    print("PASS: Stored data remains available across connections.")