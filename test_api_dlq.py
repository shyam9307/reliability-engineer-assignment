import uuid

from fastapi.testclient import TestClient

import main


def test_dead_letter_failure_and_successful_replay():
    original_dependency = main.mock_downstream_dependency

    def always_fail(force_failure=False, audio_ref="synthetic"):
        raise TimeoutError("downstream_timeout")

    # Generate a fresh ID so previous test runs cannot affect this one.
    event_id = f"dlq-replay-test-{uuid.uuid4().hex}"

    try:
        main.mock_downstream_dependency = always_fail

        # Reset the circuit breaker before testing.
        main.circuit_breaker.state = "CLOSED"
        main.circuit_breaker.failure_count = 0
        main.circuit_breaker.opened_at = None
        main.circuit_breaker.trial_in_progress = False

        with TestClient(main.app) as client:

            # Step A: Force a failure.
            failure_response = client.post(
                "/pipeline/process",
                json={
                    "event_id": event_id,
                    "audio_ref": "synthetic",
                },
            )

            assert failure_response.status_code == 503, (
                f"Expected 503, got {failure_response.status_code}: "
                f"{failure_response.text}"
            )

            # Step B: Confirm the event was saved to the DLQ.
            queue_response = client.get("/pipeline/dead-letters")
            assert queue_response.status_code == 200

            queued_events = queue_response.json()["events"]

            assert any(
                event["event_id"] == event_id
                for event in queued_events
            ), f"Failed event was not found in queue: {queued_events}"

            print("PASS: Failed event was saved to the dead-letter queue.")

            # Step C: Make the dependency succeed.
            main.mock_downstream_dependency = (
                lambda force_failure=False, audio_ref="synthetic": {
                    "transcript": "synthetic transcript",
                    "response_audio_ref": "synthetic",
                }
            )

            replay_response = client.post(
                f"/pipeline/replay/{event_id}"
            )

            assert replay_response.status_code == 200, (
                f"Expected 200, got {replay_response.status_code}: "
                f"{replay_response.text}"
            )

            replay_body = replay_response.json()

            assert replay_body["status"] == "ok"
            assert replay_body["event_id"] == event_id

            print("PASS: Dead-letter event replayed successfully.")

            # Step D: Confirm the event was removed from the DLQ.
            final_queue_response = client.get("/pipeline/dead-letters")
            remaining_events = final_queue_response.json()["events"]

            assert not any(
                event["event_id"] == event_id
                for event in remaining_events
            ), f"Replayed event remains in queue: {remaining_events}"

            print(
                "PASS: Successfully replayed event was removed "
                "from the queue."
            )

    finally:
        main.mock_downstream_dependency = original_dependency