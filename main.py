import random
import time
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from observability import (
    MetricsMiddleware,
    cloudwatch_publisher,
    health_response,
    metrics_response,
)

from storage import (
    initialize_database,
    get_processed_event,
    save_processed_event,
    save_dead_letter,
    get_dead_letter,
    list_dead_letters,
    increment_dead_letter_replay_count,
    delete_dead_letter,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    print("SQLite database initialized successfully.")

    cloudwatch_publisher.start()
    try:
        yield
    finally:
        cloudwatch_publisher.stop()


app = FastAPI(
    title="Reliable Pipeline Service",
    lifespan=lifespan,
)

app.add_middleware(MetricsMiddleware)


@app.get("/health")
def health():
    return health_response()


@app.get("/metrics")
def get_metrics():
    return metrics_response()


class CircuitBreaker:
    """
    Simple thread-safe circuit breaker.

    CLOSED: Allow calls.
    OPEN: Block calls temporarily.
    HALF_OPEN: Allow one trial call after the recovery timeout.
    """

    def __init__(self, failure_threshold=3, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.opened_at = None
        self.trial_in_progress = False
        self.lock = threading.Lock()

    def allow_request(self):
        with self.lock:
            if self.state == "OPEN":
                elapsed = time.monotonic() - self.opened_at

                if elapsed < self.recovery_timeout:
                    return False

                self.state = "HALF_OPEN"
                self.trial_in_progress = False
                print("Circuit breaker: OPEN -> HALF_OPEN")

            if self.state == "HALF_OPEN":
                if self.trial_in_progress:
                    return False

                self.trial_in_progress = True

            return True

    def record_success(self):
        with self.lock:
            if self.state != "CLOSED":
                print(f"Circuit breaker: {self.state} -> CLOSED")

            self.state = "CLOSED"
            self.failure_count = 0
            self.opened_at = None
            self.trial_in_progress = False

    def record_failure(self):
        with self.lock:
            self.failure_count += 1
            self.trial_in_progress = False

            if self.state == "HALF_OPEN":
                self.state = "OPEN"
                self.opened_at = time.monotonic()
                print("Circuit breaker: HALF_OPEN -> OPEN")
                return

            if (
                self.state == "CLOSED"
                and self.failure_count >= self.failure_threshold
            ):
                self.state = "OPEN"
                self.opened_at = time.monotonic()
                print("Circuit breaker: CLOSED -> OPEN")


circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=10,
)


class PipelineRequest(BaseModel):
    event_id: str
    audio_ref: str


def mock_downstream_dependency(force_failure: bool = False):
    """
    Simulate a downstream dependency.

    Latency follows a lognormal distribution.
    A selected request can simulate a persistent downstream outage.
    Other requests have a 20% transient failure probability per attempt.
    """
    delay = random.lognormvariate(5.7, 0.60) / 1000
    time.sleep(delay)

    if force_failure:
        raise TimeoutError("downstream_timeout")

    if random.random() < 0.20:
        raise TimeoutError("downstream_timeout")


def call_dependency_with_retries(
    max_attempts: int = 3,
    force_failure: bool = False,
):
    """
    Retry dependency failures using exponential backoff and jitter.

    A forced failure represents a persistent outage for the logical
    request, so all retry attempts fail.
    """
    for attempt in range(max_attempts):
        try:
            print(f"Dependency attempt {attempt + 1}/{max_attempts}")

            mock_downstream_dependency(force_failure=force_failure)

            print(f"Dependency succeeded on attempt {attempt + 1}")
            return

        except TimeoutError:
            print(
                f"Dependency attempt {attempt + 1} failed: "
                "downstream_timeout"
            )

            if attempt == max_attempts - 1:
                print("All dependency attempts failed")
                raise

            backoff_seconds = 0.1 * (2 ** attempt)
            jitter_seconds = random.uniform(0, 0.05)
            wait_seconds = backoff_seconds + jitter_seconds

            print(f"Retrying in {wait_seconds:.3f} seconds")
            time.sleep(wait_seconds)

def ensure_circuit_allows_request():
    if not circuit_breaker.allow_request():
        print("Request rejected: circuit breaker is open")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "reason": "downstream_timeout",
            },
        )

def process_dependency_or_raise(event_id: str, audio_ref: str):
    """Call the dependency, record breaker state, and persist failures."""
    ensure_circuit_allows_request()

    # Select approximately 20% of logical requests for persistent failure.
    force_failure = random.random() < 0.20

    try:
        call_dependency_with_retries(force_failure=force_failure)
        circuit_breaker.record_success()

    except TimeoutError:
        circuit_breaker.record_failure()

        save_dead_letter(
            event_id=event_id,
            audio_ref=audio_ref,
            reason="downstream_timeout",
        )

        print(
            f"event_id={event_id} status=error "
            "reason=downstream_timeout saved_to_dlq=true"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "reason": "downstream_timeout",
            },
        )

def create_success_response(start_time: float):
    return {
        "status": "ok",
        "transcript": "synthetic transcript",
        "response_audio_ref": "synthetic",
        "latency_ms": round((time.perf_counter() - start_time) * 1000),
    }


@app.post("/pipeline/process")
def process_pipeline(request: PipelineRequest):
    start_time = time.perf_counter()

    # Return the original result for an identical previously processed event.
    existing_event = get_processed_event(request.event_id)

    if existing_event is not None:
        if existing_event["audio_ref"] != request.audio_ref:
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "error",
                    "reason": "event_id_conflict",
                },
            )

        print(
            f"event_id={request.event_id} "
            "status=ok idempotent_replay=true"
        )
        return existing_event["response"]

    # A failed event ID must not be reused for different input.
    failed_event = get_dead_letter(request.event_id)
    if failed_event is not None and failed_event["audio_ref"] != request.audio_ref:
        raise HTTPException(
            status_code=409,
            detail={
                "status": "error",
                "reason": "event_id_conflict",
            },
        )

    process_dependency_or_raise(request.event_id, request.audio_ref)

    response = create_success_response(start_time)

    save_processed_event(
        request.event_id,
        request.audio_ref,
        response,
    )

    # If a previously failed event succeeds through this endpoint, clear its DLQ entry.
    delete_dead_letter(request.event_id)

    print(
        f"event_id={request.event_id} "
        f"status=ok latency_ms={response['latency_ms']}"
    )
    return response


@app.get("/pipeline/dead-letters")
def get_dead_letters():
    """Return the events currently waiting in the dead-letter queue."""
    return {
        "count": len(list_dead_letters()),
        "events": list_dead_letters(),
    }


@app.post("/pipeline/replay/{event_id}")
def replay_dead_letter(event_id: str):
    """Retry one failed event stored in the dead-letter queue."""
    event = get_dead_letter(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "reason": "dead_letter_not_found",
            },
        )

    # If it was already processed, clean up any stale DLQ record.
    processed = get_processed_event(event_id)
    if processed is not None:
        delete_dead_letter(event_id)
        return {
            "status": "ok",
            "event_id": event_id,
            "message": "Event was already processed; stale dead-letter entry removed.",
            "response": processed["response"],
        }

    ensure_circuit_allows_request()
    increment_dead_letter_replay_count(event_id)

    start_time = time.perf_counter()
    try:
        call_dependency_with_retries()
        circuit_breaker.record_success()
    except TimeoutError:
        circuit_breaker.record_failure()
        save_dead_letter(
            event_id=event_id,
            audio_ref=event["audio_ref"],
            reason="downstream_timeout",
        )
        print(
            f"event_id={event_id} replay_failed=true "
            "reason=downstream_timeout saved_to_dlq=true"
        )
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "reason": "downstream_timeout",
            },
        )

    response = create_success_response(start_time)
    save_processed_event(event_id, event["audio_ref"], response)
    delete_dead_letter(event_id)

    print(
        f"event_id={event_id} replay_succeeded=true "
        f"latency_ms={response['latency_ms']}"
    )
    return {
        "status": "ok",
        "event_id": event_id,
        "message": "Dead-letter event replayed successfully.",
        "response": response,
    }