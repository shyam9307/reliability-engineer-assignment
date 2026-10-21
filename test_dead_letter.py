from storage import (
    initialize_database,
    save_dead_letter,
    get_dead_letter,
    list_dead_letters,
    increment_dead_letter_replay_count,
    delete_dead_letter,
)

# Step 1: Initialize the database.
initialize_database()
print("PASS: Database initialized successfully.")

# Step 2: Save a failed event.
event_id = "dlq-test-001"

save_dead_letter(
    event_id=event_id,
    audio_ref="synthetic",
    reason="downstream_timeout",
)

print("PASS: Failed event saved to the dead-letter queue.")

# Step 3: Retrieve the saved event.
event = get_dead_letter(event_id)

assert event is not None
assert event["event_id"] == event_id
assert event["audio_ref"] == "synthetic"
assert event["reason"] == "downstream_timeout"
assert event["replay_count"] == 0

print("PASS: Saved event retrieved with correct details.")

# Step 4: Check that the event appears in the queue.
events = list_dead_letters()

assert any(item["event_id"] == event_id for item in events)

print("PASS: Event appears in the dead-letter queue.")

# Step 5: Increment the replay counter.
increment_dead_letter_replay_count(event_id)

event = get_dead_letter(event_id)

assert event["replay_count"] == 1

print("PASS: Replay counter incremented successfully.")

# Step 6: Delete the test event.
delete_dead_letter(event_id)

assert get_dead_letter(event_id) is None

print("PASS: Deleted event no longer appears in the queue.")

print("\nAll dead-letter storage tests passed!")