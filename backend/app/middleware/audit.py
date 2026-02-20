import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("audit")


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit purposes."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={process_time:.3f}s "
            f"client={request.client.host if request.client else 'unknown'}"
        )
        return response
