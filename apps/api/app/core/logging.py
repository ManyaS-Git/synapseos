"""Centralized logging configuration for SynapseOS.

Provides structured logging with:
- Colored console output for development
- JSON structured logs for production
- Rotating file logs
- Request logging middleware
- Error capture with context
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a named structlog logger.

    Args:
        name: Logger name, typically a dotted module path.

    Returns:
        A bound structlog logger instance.
    """
    return structlog.get_logger(name)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "console",
    log_file: str | None = None,
    log_max_bytes: int = 10_485_760,
    log_backup_count: int = 5,
) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — "console" for human-readable, "json" for machine-readable.
        log_file: Optional file path for rotating log output.
        log_max_bytes: Maximum size per log file before rotation.
        log_backup_count: Number of rotated log files to keep.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [console_handler]

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = structlog.get_logger("synapseos.logging")
    logger.info(
        "Logging configured",
        level=log_level,
        format=log_format,
        file=log_file,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request with timing and status."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Any:
        """Process request, log timing, and return response."""
        logger = structlog.get_logger("synapseos.http")
        start_time = time.perf_counter()

        request_id = request.headers.get("X-Request-ID", "")
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info("Request started")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        log_method = logger.info if response.status_code < 400 else logger.warning

        log_method(
            "Request completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers["X-Process-Time"] = f"{duration_ms:.2f}"
        return response


def register_error_handlers(app: FastAPI) -> None:
    """Register global error handlers on the FastAPI app."""

    logger = structlog.get_logger("synapseos.errors")

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions with structured logging."""
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_msg=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "status": 500,
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        """Handle 404 Not Found."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Not found",
                "status": 404,
            },
        )


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app."""
    from starlette.middleware.cors import CORSMiddleware

    from app.core.config import settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
