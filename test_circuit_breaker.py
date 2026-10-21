import time

from main import CircuitBreaker


def test_circuit_breaker_opens_after_three_failures():
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2,
    )

    # Initially, requests should be allowed.
    assert breaker.allow_request() is True

    # Record three consecutive failures.
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()

    # The circuit should now be OPEN.
    assert breaker.state == "OPEN"

    # Requests should be blocked while the circuit is OPEN.
    assert breaker.allow_request() is False

    print("PASS: Circuit opens after three failures.")


def test_circuit_breaker_recovers_after_timeout():
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1,
    )

    # Open the circuit.
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()

    assert breaker.state == "OPEN"

    # Wait for the recovery timeout.
    time.sleep(1.1)

    # One trial request should now be allowed.
    assert breaker.allow_request() is True
    assert breaker.state == "HALF_OPEN"

    # Simulate a successful trial request.
    breaker.record_success()

    # The circuit should close again.
    assert breaker.state == "CLOSED"
    assert breaker.failure_count == 0

    print("PASS: Circuit recovers and closes after success.")


if __name__ == "__main__":
    test_circuit_breaker_opens_after_three_failures()
    test_circuit_breaker_recovers_after_timeout()

    print("\nAll circuit breaker tests passed!")