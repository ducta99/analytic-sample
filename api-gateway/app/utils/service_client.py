"""HTTP client utility for propagating request IDs to downstream services."""

from typing import Optional, Dict, Any
import httpx

from app.middleware.request_id import get_request_id


async def call_downstream_service(
    service_url: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> httpx.Response:
    """
    Call a downstream service and propagate request ID.

    Args:
        service_url: Full URL to downstream service endpoint
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        json_data: JSON data to send in request body
        params: Query parameters
        **kwargs: Additional arguments to pass to httpx

    Returns:
        Response from downstream service
    """
    # Get current request ID
    request_id = get_request_id()

    # Prepare headers
    headers = kwargs.get("headers", {})
    if request_id:
        headers["X-Request-ID"] = request_id

    # Update headers in kwargs
    kwargs["headers"] = headers
    
    # Add json data if provided
    if json_data is not None:
        kwargs["json"] = json_data
    
    # Add query params if provided
    if params is not None:
        kwargs["params"] = params

    # Make request
    async with httpx.AsyncClient() as client:
        return await client.request(method, service_url, **kwargs)
