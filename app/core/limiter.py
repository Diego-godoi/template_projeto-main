"""
Instância compartilhada do Limiter do slowapi.

Mantida em módulo separado para evitar import circular entre `main.py`
e os módulos de endpoints que precisam do decorador `@limiter.limit`.

Em produção/Docker, o storage é o Redis (REDIS_URL), garantindo que o
rate limiting funcione corretamente com múltiplos workers. Em ambiente
local/dev (sem REDIS_URL definida), cai no storage em memória (padrão).
"""

from typing import Final

import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def get_rate_limit_key(request: Request) -> str:
    """Use the authenticated subject when available, otherwise the client IP."""
    remote_address = get_remote_address(request)
    authorization = request.headers.get("Authorization", "")

    if authorization.lower().startswith("bearer "):
        try:
            payload = jwt.decode(
                authorization[7:].strip(),
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
            if payload.get("sub"):
                return f"user:{payload['sub']}"
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError):
            pass

    return f"ip:{remote_address}"


GLOBAL_LIMIT: Final[str] = "100/minute"
AUTH_LIMIT: Final[str] = "5/minute"
PASSWORD_RESET_LIMIT: Final[str] = "3/minute"
PUBLIC_LIMIT: Final[str] = "30/minute"
HEAVY_LIMIT: Final[str] = "20/minute"
UPLOAD_LIMIT: Final[str] = "20/minute"

limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[GLOBAL_LIMIT],
    storage_uri=settings.REDIS_URL or "memory://",
)
