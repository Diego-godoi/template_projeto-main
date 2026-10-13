"""
Configuração central de logging da aplicação.

Filosofia Twelve-Factor App: todos os logs são tratados como um fluxo contínuo
de eventos direcionados ao stdout, delegando persistência e rotação ao daemon
do Docker. Zero uso de FileHandler, RotatingFileHandler ou escrita em disco.

A estrutura (handlers, formato, loggers) vive em ``logging_config.json``, que o
Uvicorn carrega no boot via ``--log-config``. Este módulo só aplica o nível de
log definido pelas settings da aplicação.
"""

import json
import logging
import logging.config
from contextvars import ContextVar
from pathlib import Path

__all__ = ["REQUEST_ID", "RequestContextFilter", "setup_logging"]

REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)

_CONFIG_PATH = Path(__file__).with_name("logging_config.json")
_ALLOWED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class RequestContextFilter(logging.Filter):
    """Adiciona o identificador da requisição a todo registro emitido."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID.get() or "-"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Aplica o nível de log da aplicação.

    Se a aplicação subiu sem ``--log-config`` (testes, scripts), carrega o
    mesmo JSON como fallback para que os handlers existam.

    Args:
        log_level: DEBUG, INFO, WARNING, ERROR ou CRITICAL. Padrão: "INFO".
    """
    level = log_level.upper()
    if level not in _ALLOWED_LEVELS:
        raise ValueError(
            f"Nível de log inválido: {log_level!r}. "
            f"Valores aceitos: {', '.join(sorted(_ALLOWED_LEVELS))}"
        )

    app_logger = logging.getLogger("app")
    if not app_logger.handlers:
        with _CONFIG_PATH.open(encoding="utf-8") as config_file:
            logging.config.dictConfig(json.load(config_file))

    # uvicorn.error e uvicorn.access herdam do logger "uvicorn"/pai.
    for name in ("app", "uvicorn"):
        logging.getLogger(name).setLevel(level)

    app_logger.info(
        "Sistema de logging inicializado — nível: %s, destino: stdout", level
    )
