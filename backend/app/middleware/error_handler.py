"""
Global error handling middleware.

Never exposes stack traces to users. Returns structured error responses.
"""

import logging
import traceback
import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns structured error responses."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                f"Unhandled error [request_id={request_id}] "
                f"{request.method} {request.url.path}: {exc}",
                exc_info=True,
            )

            # Never expose stack traces in production
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests for monitoring (never logs sensitive data)."""

    async def dispatch(self, request: Request, call_next):
        start = datetime.now(timezone.utc)
        response = await call_next(request)
        duration = (datetime.now(timezone.utc) - start).total_seconds()

        # Only log API calls, skip static assets
        if request.url.path.startswith("/api"):
            logger.info(
                f"{request.method} {request.url.path} → {response.status_code} "
                f"({duration:.3f}s)"
            )

        return response
