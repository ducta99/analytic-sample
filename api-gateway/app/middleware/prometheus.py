"""Prometheus metrics middleware for FastAPI."""

from prometheus_client import Counter, Histogram
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics on HTTP requests."""

    def __init__(self, app, skip_paths=None):
        super().__init__(app)
        self.skip_paths = skip_paths or []

    async def dispatch(
        self, request: Request, call_next
    ) -> Response:
        """
        Track HTTP request metrics.

        Args:
            request: The HTTP request
            call_next: Next middleware/endpoint

        Returns:
            Response with metrics recorded
        """
        # Skip metrics collection for health checks and metrics endpoint
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)

        # Get or set labels
        method = request.method
        endpoint = request.url.path

        # Normalize endpoint (remove IDs for better grouping)
        if endpoint.startswith("/api/"):
            parts = endpoint.split("/")
            # Replace numeric IDs and UUIDs with placeholder
            for i, part in enumerate(parts):
                if part and (part.isdigit() or "-" in part and len(part) == 36):
                    parts[i] = "{id}"
            endpoint = "/".join(parts)

        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            # Record metrics
            from shared.utils.metrics import (
                request_count,
                request_duration,
            )

            duration = time.time() - start_time

            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
