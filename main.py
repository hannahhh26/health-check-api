import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

app = FastAPI()

logger = logging.getLogger("health-check-api")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of application HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Application HTTP request duration in seconds",
    ["method", "endpoint"],
)


def record_request_metrics(request: Request, status_code: int, duration: float):
    if request.url.path == "/metrics":
        return

    route = request.scope.get("route")
    endpoint = getattr(route, "path", "unmatched")

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - start_time
        record_request_metrics(request, 500, duration)

        logger.error(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "ERROR",
                    "event": "request_failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": round(duration * 1000, 2),
                }
            ),
            exc_info=True,
        )
        raise

    duration = time.perf_counter() - start_time
    record_request_metrics(request, response.status_code, duration)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )
    )

    return response


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/info")
def get_info():
    return {"environment": os.getenv("APP_ENV", "local")}


@app.get("/metrics")
def get_metrics():
    return Response(
        content=generate_latest(),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )