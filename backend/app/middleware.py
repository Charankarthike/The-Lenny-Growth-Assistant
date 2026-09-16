"""
Custom middleware for logging, error handling, and request tracking.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from app.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        # Log incoming request
        start_time = time.time()
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Add headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=f"{process_time:.2f}"
            )
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time_ms=f"{process_time:.2f}"
            )
            raise
        finally:
            # Clear context
            structlog.contextvars.clear_contextvars()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and return structured error responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            
            logger.error(
                "unhandled_exception",
                error_type=type(e).__name__,
                error_message=str(e),
                path=request.url.path,
                correlation_id=correlation_id,
                exc_info=True
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "internal_server_error",
                        "message": "An unexpected error occurred. Please try again later.",
                        "correlation_id": correlation_id
                    }
                }
            )
