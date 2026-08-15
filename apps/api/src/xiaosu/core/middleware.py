import logging
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from xiaosu.core.logging import new_request_id, request_id_context

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        token = request_id_context.set(request_id)
        started_at = perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((perf_counter() - started_at) * 1000)
            logger.info(
                "%s %s completed status=%s duration_ms=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_context.reset(token)
