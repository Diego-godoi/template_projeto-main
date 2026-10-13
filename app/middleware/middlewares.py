import logging
import time
from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import REQUEST_ID

__all__ = ["LoggingMiddleware"]

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware que loga o ciclo de vida de cada requisição HTTP de entrada.

    Registra duas mensagens por requisição:
    - DEBUG ao receber: método e path.
    - INFO/WARNING ao finalizar: método, path, status HTTP e duração em ms.

    Respostas com status >= 400 são registradas como WARNING para facilitar
    a triagem de erros de cliente em ambientes de produção.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        request_id = self._request_id_from_header(request)
        request_id_token = REQUEST_ID.set(request_id)
        request.state.request_id = request_id
        client_host = request.client.host if request.client else "-"

        try:
            logger.debug(
                "Requisição %s %s recebida do cliente %s",
                request.method,
                request.url.path,
                client_host,
            )

            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            log_fn = (
                logger.warning if response.status_code >= 400 else logger.info
            )
            log_fn(
                "Requisição %s %s do cliente %s finalizada com status %d em %.1fms",
                request.method,
                request.url.path,
                client_host,
                response.status_code,
                duration_ms,
            )

            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            REQUEST_ID.reset(request_id_token)

    @staticmethod
    def _request_id_from_header(request: Request) -> str:
        request_id_header = request.headers.get("X-Request-ID")
        if request_id_header:
            try:
                return str(UUID(request_id_header))
            except ValueError:
                logger.warning(
                    "X-Request-ID inválido recebido em %s %s; um novo identificador será gerado",
                    request.method,
                    request.url.path,
                )
        return str(uuid4())
