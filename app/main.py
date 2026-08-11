import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import api, core
from app.core.limiter import limiter
from app.error import CustomException, DatabaseException, ValidationException

logger = logging.getLogger(__name__)

if core.settings.DEBUG:
    app = FastAPI(title=core.settings.PROJECT_NAME)
else:
    app = FastAPI(docs_url=None, redocs_url=None, openapi_url=None)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


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


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    """
    Captura falhas críticas lançadas pela camada do banco de dados e as traduz
    para o requisitante de forma protegida, evitando vazamento arquitetural na stacktrace.
    """
    logger.error(
        f"Erro no BD detectado pela requisição {request.url}: {exc.detail}"
    )

    # Podemos suprimir e mascarar os detalhes internos do banco para o usuário final
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
    """
    logger.error(
        f"Erro personalizado detectado pela requisição {request.url}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(api.routers, prefix=core.settings.API_URL_PREFIX)
