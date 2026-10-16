"""
Configuração central de logging da aplicação.

Filosofia Twelve-Factor App: todos os logs são tratados como um fluxo contínuo
de eventos direcionados ao stdout, delegando persistência e rotação ao daemon
do Docker. Zero uso de FileHandler, RotatingFileHandler ou escrita em disco.

A configuração inteira vive neste módulo via ``dictConfig``, dispensando arquivo
JSON externo e a flag ``--log-config`` do Uvicorn. Basta chamar
``setup_logging()`` antes de criar o ``FastAPI()``, e o dictConfig sobrescreve
os loggers ``uvicorn``, ``uvicorn.error`` e ``uvicorn.access`` já registrados
pelo servidor.
"""

import logging
import logging.config
from contextvars import ContextVar

__all__ = ["REQUEST_ID", "RequestContextFilter", "setup_logging"]

REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)

_ALLOWED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class RequestContextFilter(logging.Filter):
    """Adiciona o identificador da requisição a todo registro emitido."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID.get() or "-"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configura todo o sistema de logging via ``dictConfig``.

    Deve ser chamada **antes** de ``app = FastAPI(...)`` no ``main.py``.
    Isso garante que, ao importar a aplicação, o Uvicorn já encontra os
    loggers ``uvicorn``, ``uvicorn.error`` e ``uvicorn.access`` configurados
    pelo nosso dictConfig, sobrescrevendo a configuração padrão dele.

    O nível pode ser controlado pela variável de ambiente ``LOG_LEVEL``
    (lida pelo pydantic-settings em ``config.py``), sem necessidade de flag.

    Args:
        log_level: DEBUG, INFO, WARNING, ERROR ou CRITICAL. Padrão: "INFO".
    """
    level = log_level.upper()
    if level not in _ALLOWED_LEVELS:
        raise ValueError(
            f"Nível de log inválido: {log_level!r}. "
            f"Valores aceitos: {', '.join(sorted(_ALLOWED_LEVELS))}"
        )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {
                    "()": "app.core.logging_config.RequestContextFilter",
                },
            },
            "formatters": {
                "natural": {
                    "format": (
                        "%(asctime)s [%(levelname)s] [%(name)s]"
                        " [request_id=%(request_id)s] %(message)s"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "natural",
                    "filters": ["request_context"],
                },
            },
            "loggers": {
                "app": {
                    "handlers": ["stdout"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["stdout"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["stdout"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": [],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["stdout"],
                "level": "WARNING",
            },
        }
    )

    logging.getLogger("app").info(
        "Sistema de logging inicializado — nível: %s, destino: stdout", level
    )
