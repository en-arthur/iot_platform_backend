import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Default limit: 200 requests per minute per IP
DEFAULT_RATE_LIMIT = 200
WINDOW_SECONDS = 60
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB payload ceiling


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window rate limiter and request payload size guard."""

    def __init__(self, app, max_requests: int = DEFAULT_RATE_LIMIT, max_body_bytes: int = MAX_CONTENT_LENGTH):
        super().__init__(app)
        self.max_requests = max_requests
        self.max_body_bytes = max_body_bytes
        self.client_records: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclude health endpoints and pre-flight CORS OPTIONS from rate limiting
        if request.url.path in ("/health", "/api/v1/health") or request.method == "OPTIONS":
            return await call_next(request)

        # 1. Payload size guard
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload Too Large: maximum allowed request body is 10MB"},
            )

        # 2. Rate limiting check
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - WINDOW_SECONDS

        # Prune old timestamps
        history = [ts for ts in self.client_records[client_ip] if ts > window_start]
        self.client_records[client_ip] = history

        if len(history) >= self.max_requests:
            retry_after = int(WINDOW_SECONDS - (now - history[0])) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests: rate limit exceeded"},
                headers={
                    "Retry-After": str(max(1, retry_after)),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Record this request
        self.client_records[client_ip].append(now)
        remaining = max(0, self.max_requests - len(self.client_records[client_ip]))

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
