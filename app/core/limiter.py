"""
Instância compartilhada do Limiter do slowapi.

Mantida em módulo separado para evitar import circular entre `main.py`
e os módulos de endpoints que precisam do decorador `@limiter.limit`.

Em produção/Docker, o storage é o Redis (REDIS_URL), garantindo que o
rate limiting funcione corretamente com múltiplos workers. Em ambiente
local/dev (sem REDIS_URL definida), cai no storage em memória (padrão).
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_redis_url = os.getenv("REDIS_URL")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_redis_url if _redis_url else "memory://",
)
