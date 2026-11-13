import time
import uuid
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.health import check_health
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import APIError
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimiterMiddleware
import logging

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]"
    )
    # Restore projects/specs/files persisted in Supabase (no-op without a key).
    try:
        from app.db.supabase_store import hydrate

        hydrate()
    except Exception as exc:  # never block startup on the database
        logger.warning(f"Supabase hydration skipped: {exc}")

    # Keep the Render-hosted broker warm. It sleeps after ~15 minutes idle, and
    # the first publish after that fails the WebSocket handshake.
    keepalive_task = None
    if settings.MQTT_USE_TLS:
        import asyncio as _asyncio

        from app.services.mqtt_service import mqtt_service

        async def _mqtt_keepalive():
            while True:
                try:
                    await mqtt_service.publish(
                        "system/keepalive", {"ts": time.time()}, attempts=2
                    )
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug(f"MQTT keepalive failed: {exc}")
                await _asyncio.sleep(300)

        keepalive_task = _asyncio.create_task(_mqtt_keepalive())

    yield

    if keepalive_task:
        keepalive_task.cancel()
        with suppress(Exception):
            await keepalive_task
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Add Rate Limiting and Payload Protection Middleware
app.add_middleware(RateLimiterMiddleware)

# Configure CORS only for frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()

    # Pass request_id via response header
    response: Response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
        extra={"request_id": request_id},
    )
    return response


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail},
    )


# Root health route directly at /health as well as /api/v1/health
app.add_api_route("/health", check_health, methods=["GET"], tags=["Health"])

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
