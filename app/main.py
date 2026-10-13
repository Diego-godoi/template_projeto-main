import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import api, core
from app.core.limiter import limiter
from app.core.logging_config import REQUEST_ID, setup_logging
from app.error import CustomException, DatabaseException, ValidationException
from app.middleware import LoggingMiddleware

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    """Retorna o ID da requisição do state da requisição."""
    return getattr(request.state, "request_id", "-")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação FastAPI.

    O logging é inicializado aqui para garantir que qualquer mensagem emitida
    durante o startup já use o formato e nível configurados corretamente.
    """
    setup_logging(core.settings.LOG_LEVEL)
    logger.info(
        "Aplicação '%s' inicializada em modo %s",
        core.settings.PROJECT_NAME,
        "DEBUG" if core.settings.DEBUG else "PRODUÇÃO",
    )
    yield
    logger.info("Aplicação '%s' encerrada", core.settings.PROJECT_NAME)


if core.settings.DEBUG:
    app = FastAPI(title=core.settings.PROJECT_NAME, lifespan=lifespan)
else:
    app = FastAPI(
        docs_url=None, redocs_url=None, openapi_url=None, lifespan=lifespan
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationException)
async def validation_exception_handler(
    request: Request, exc: ValidationException
):
    """
    Captura erros de validação acumulados e retorna todos de uma vez
    no formato padrão do FastAPI/Pydantic.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    formatted_errors = []
    for err in exc.errors():
        msg = err.get("msg", "")
        if msg.startswith("Value error, "):
            msg = msg.removeprefix("Value error, ")
        formatted_errors.append(
            {
                "loc": err.get("loc", []),
                "msg": msg,
                "type": err.get("type", "value_error"),
            }
        )
    return JSONResponse(status_code=422, content={"detail": formatted_errors})


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    """
    Captura falhas críticas lançadas pela camada do banco de dados e as traduz
    para o requisitante de forma protegida, evitando vazamento arquitetural na stacktrace.
    """
    logger.error(
        "Falha de banco de dados na requisição %s %s com status %d",
        request.method,
        request.url.path,
        exc.status_code,
    )

    # Suprime os detalhes internos do banco para o usuário final
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": "Ocorreu um erro no banco de dados. Contate o administrador."
        },
    )


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """
    Captura exceções personalizadas e as traduz
    para o requisitante de forma protegida, evitando vazamento arquitetural na stacktrace.

    Erros de cliente (< 500) já são logados pelo serviço e pelo middleware,
    então aqui ficam em DEBUG; só falhas de servidor (>= 500) sobem para ERROR.
    """
    level = logging.ERROR if exc.status_code >= 500 else logging.DEBUG
    logger.log(
        level,
        "Exceção personalizada na requisição %s %s com status %d",
        request.method,
        request.url.path,
        exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
):
    formatted_errors = []
    for err in exc.errors():
        msg = err.get("msg", "")
        if msg.startswith("Value error, "):
            msg = msg.removeprefix("Value error, ")
        formatted_errors.append(
            {
                "loc": ["body", *err.get("loc", [])],
                "msg": msg,
                "type": err.get("type", "value_error"),
            }
        )
    return JSONResponse(status_code=422, content={"detail": formatted_errors})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Trata qualquer exceção não prevista e responde 500.

    Este handler roda no ServerErrorMiddleware, fora do LoggingMiddleware:
    o ContextVar já foi resetado e o header X-Request-ID não é adicionado
    pelo middleware. Por isso o ID é reativado para o log e enviado no header
    diretamente na resposta.
    """
    request_id = _request_id(request)
    token = REQUEST_ID.set(request_id)
    try:
        logger.error(
            "Exceção não tratada na requisição %s %s",
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
    finally:
        REQUEST_ID.reset(token)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Ocorreu um erro interno. Contate o administrador."
        },
        headers={"X-Request-ID": request_id},
    )


app.include_router(api.routers, prefix=core.settings.API_URL_PREFIX)
