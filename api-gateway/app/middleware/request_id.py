"""Request ID tracking middleware for distributed tracing."""

import uuid
import contextvars
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variable to store request ID
request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_context.get("")


def set_request_id(request_id: str) -> None:
    """Set the request ID in context."""
    request_id_context.set(request_id)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates and tracks request IDs for distributed tracing."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Generate request ID from header or create new one.

        Args:
            request: The HTTP request
            call_next: Next middleware/endpoint

        Returns:
            Response with request ID header
        """
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in context for access throughout request lifecycle
        set_request_id(request_id)

        # Add request ID to request state for access in route handlers
        request.state.request_id = request_id

        # Process request with downstream services
        response = await call_next(request)

        # Add request ID to response header
        response.headers["X-Request-ID"] = request_id

        return response
