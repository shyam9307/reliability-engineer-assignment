import logging
import os
import threading
import time
from collections import Counter

import boto3
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

METRIC_NAMESPACE = "ReliablePipeline"
PUBLISH_INTERVAL_SECONDS = 30


class RequestMetrics:
    """Thread-safe in-memory HTTP request metrics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counts = Counter()
        self._latencies = []
        self._active_requests = 0

    def start_request(self):
        with self._lock:
            self._active_requests += 1
            return self._active_requests

    def finish_request(self, method, path, status_code, duration_ms):
        key = f"{method} {path} {status_code}"

        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            self._counts[key] += 1
            self._latencies.append(duration_ms)

            # Bound memory usage for this demonstration.
            if len(self._latencies) > 10000:
                self._latencies = self._latencies[-5000:]

    def snapshot(self):
        with self._lock:
            counts = dict(self._counts)
            latencies = sorted(self._latencies)
            active_requests = self._active_requests

        def percentile(p):
            if not latencies:
                return None
            index = round((len(latencies) - 1) * p)
            return round(latencies[index], 2)

        return {
            "request_counts": counts,
            "total_requests": sum(counts.values()),
            "active_requests": active_requests,
            "latency_ms": {
                "p50": percentile(0.50),
                "p90": percentile(0.90),
                "p99": percentile(0.99),
            },
        }


metrics = RequestMetrics()


class CloudWatchPublisher:
    """Optionally publish concurrent-request metrics to CloudWatch."""

    def __init__(self):
        self.enabled = (
            os.getenv("CLOUDWATCH_METRICS_ENABLED", "false").lower() == "true"
        )
        self.cluster_name = os.getenv("ECS_CLUSTER_NAME")
        self.service_name = os.getenv("ECS_SERVICE_NAME")
        self._thread = None
        self._stop_event = threading.Event()
        self._client = None

    def start(self):
        if not self.enabled:
            logger.info("CloudWatch custom metric publishing is disabled.")
            return

        if not self.cluster_name or not self.service_name:
            logger.error(
                "CloudWatch publishing enabled, but ECS_CLUSTER_NAME or "
                "ECS_SERVICE_NAME is missing. Publishing remains disabled."
            )
            self.enabled = False
            return

        try:
            # In ECS, boto3 obtains temporary credentials from the task role.
            self._client = boto3.client("cloudwatch")
        except Exception:
            logger.exception("Could not initialize the CloudWatch client.")
            self.enabled = False
            return

        self._thread = threading.Thread(
            target=self._publish_loop,
            name="cloudwatch-metrics",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _publish_loop(self):
        while not self._stop_event.wait(PUBLISH_INTERVAL_SECONDS):
            try:
                active = metrics.snapshot()["active_requests"]
                self._client.put_metric_data(
                    Namespace=METRIC_NAMESPACE,
                    MetricData=[
                        {
                            "MetricName": "ConcurrentRequests",
                            "Dimensions": [
                                {
                                    "Name": "ClusterName",
                                    "Value": self.cluster_name,
                                },
                                {
                                    "Name": "ServiceName",
                                    "Value": self.service_name,
                                },
                            ],
                            "Value": active,
                            "Unit": "Count",
                        }
                    ],
                )
            except Exception:
                logger.exception("Failed to publish metrics to CloudWatch.")


cloudwatch_publisher = CloudWatchPublisher()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        metrics.start_request()
        start = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            # Avoid high-cardinality paths containing individual IDs.
            path = request.url.path
            if path.startswith("/pipeline/replay/"):
                path = "/pipeline/replay/{event_id}"

            metrics.finish_request(
                method=request.method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )


def health_response():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"},
    )


def metrics_response():
    return metrics.snapshot()