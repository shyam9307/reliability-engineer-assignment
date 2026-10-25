
from fastapi.testclient import TestClient

import main
from observability import metrics


def test_active_request_count_returns_to_zero():
    # Reset the metrics state for an isolated test.
    with metrics._lock:
        metrics._active_requests = 0
        metrics._counts.clear()
        metrics._latencies.clear()

    with TestClient(main.app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    # Check after the HTTP request has fully completed.
    assert metrics.snapshot()["active_requests"] == 0
