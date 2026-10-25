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

### Prerequisites

- Python 3.10 or newer
- pip

### Create a virtual environment

From the repository root, run the commands for your operating system.

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the virtual environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Linux or macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run the service

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`.

Interactive API documentation: `http://127.0.0.1:8000/docs`.

### Verify the service

In a second terminal, run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

### Run tests

```powershell
python -m pytest -v
```

### Generate the synthetic event dataset

```powershell
python .\scripts\generate_synthetic_events.py
```

The generator writes 500 synthetic events to `data/synthetic_events.jsonl`. The dataset uses a fixed random seed and contains no real borrower data.

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

The service uses a model-agnostic adapter boundary defined in `pipeline_adapter.py`. The current `MockPipelineAdapter` simulates the STT → LLM → TTS pipeline, including latency and intermittent downstream failures, so reliability features can be tested without downloading models or requiring GPU infrastructure.

To replace the mock, implement another `PipelineAdapter` that exposes the same `process(audio_ref)` interface. The implementation can call an STT model such as faster-whisper, an instruction-tuned open-weight LLM, and a TTS engine such as Piper. Keep model loading, inference, timeouts, and model-specific error handling inside the adapter rather than coupling them to the API, retry logic, circuit breaker, or dead-letter queue.

The API and resilience layer should continue to consume the adapter's result and handle failures through the existing retry, circuit-breaker, and dead-letter mechanisms. Model-specific dependencies and configuration should be documented separately, and credentials must be supplied through environment variables or an appropriate secrets manager—not hardcoded in source code.

**Current limitation:** the repository's adapter is a synthetic mock. Real model inference, GPU deployment, and end-to-end performance measurements have not yet been demonstrated.

## Limitations

This is a local reliability-engineering demonstration. It uses synthetic audio references, a synthetic transcript, and simulated latency and failures. It does not perform actual speech recognition, language generation, or speech synthesis.

## License

Licensed under the Apache License, Version 2.0. See `LICENSE`.