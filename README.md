# Reliable Pipeline Service

A Python-based mock pipeline service built for the Predixion AI and TalentX Open-Weight Collections Agent Challenge.

This project demonstrates reliability engineering for a speech-processing pipeline using a simulated downstream dependency.

## Features

- FastAPI HTTP service.
- Simulated downstream latency and failures.
- Bounded retries with exponential backoff and jitter.
- Circuit breaker for repeated dependency failures.
- SQLite persistence for processed events and dead-letter events.
- Idempotency to prevent duplicate processing.
- Dead-letter queue inspection and replay.
- Automated tests for core reliability behaviors.

## Requirements

- Python 3.10 or newer.
- pip.

## Setup

From the project directory, activate the existing virtual environment and install dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt



```

Start the API service:

```powershell
python -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

Interactive API documentation: `http://127.0.0.1:8000/docs`.

## API Endpoints

### Process an event

`POST /pipeline/process`

Example request:

```json
{
  "event_id": "event-001",
  "audio_ref": "synthetic"
}
```

A successful response includes `status`, `transcript`, `response_audio_ref`, and `latency_ms`.

A terminal simulated dependency failure returns HTTP 503 and records the event in the dead-letter queue.

Repeating the same event ID and payload returns the stored result. Reusing an event ID with a different payload returns HTTP 409.

### List dead-letter events

`GET /pipeline/dead-letters`

Returns the events currently in the dead-letter queue.

### Replay a failed event

`POST /pipeline/replay/{event_id}`

Attempts to process a previously failed event again. Successful replay stores the result and removes the event from the dead-letter queue.

## Reliability Design

The service uses bounded retries with exponential backoff and jitter. A circuit breaker temporarily blocks calls when repeated dependency failures occur.

SQLite stores processed events and failed events. Idempotency prevents duplicate processing when clients retry requests, while the dead-letter queue makes failed events available for inspection and replay.

## Testing

Run the automated tests:

```powershell
python -m pytest -v
```

Measure the simulated dependency latency distribution:

```powershell
python measure_latency.py
```

The latency script samples the configured lognormal distribution. Its results represent simulated dependency latency, not full HTTP request latency.

## Cost Considerations

The prototype runs locally using Python, FastAPI, and SQLite. The downstream dependency is mocked, so no GPU hosting or paid cloud infrastructure is required. No cloud costs were incurred or measured for the local prototype. Electricity and developer time were not separately measured.

A production deployment would add compute, model inference, storage, monitoring, networking, and data-transfer costs. A realistic estimate would require measured request volume, concurrency, model throughput, latency requirements, region, and scaling configuration.

## Replacing the Mock with Open-Weight Models

The mock dependency can be replaced with an adapter that calls open-weight speech-to-text, language-model, and text-to-speech components. The adapter should preserve the existing dependency boundary and normalize downstream timeouts and errors. This allows the retry, circuit-breaker, idempotency, and dead-letter mechanisms to remain independent of the selected models.

Model selection and hosting requirements should be evaluated using measured latency, quality, memory use, and operating cost.

## Limitations

This is a local reliability-engineering demonstration. It uses synthetic audio references, a synthetic transcript, and simulated latency and failures. It does not perform actual speech recognition, language generation, or speech synthesis.

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.