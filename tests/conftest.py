# tests/conftest.py
"""
Infraestrutura base de testes (Épico 5.1).

Estratégia de isolamento:
- Engine aponta para banco `template_teste` (banco dedicado para testes).
- Cada teste roda dentro de uma transação que sofre ROLLBACK ao final,
    garantindo que nenhum dado persista entre os testes.
- O FastAPI TestClient recebe override de `get_db` para usar a sessão de teste.

Fixtures compartilhadas:
- `_inject_session_into_factories` (autouse): injeta a sessão transacional
  do teste em TODAS as Factories SQLAlchemy.
"""

import asyncio
from urllib.parse import quote_plus

import pytest
from fastapi.security import SecurityScopes
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from app import error, models
from app.auth import get_current_payload
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app
from tests.factories import SQLALCHEMY_FACTORIES

# ---------------------------------------------------------------------------
# URL do banco de teste
# ---------------------------------------------------------------------------


def _get_test_db_url() -> str:
    user = quote_plus(settings.POSTGRES_USER)
    password = quote_plus(settings.POSTGRES_PASSWORD)
    db_test = settings.POSTGRES_DB_TEST  # lê do .env
    return (
        f"postgresql+asyncpg://{user}:{password}@"
        f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT_TEST}/{db_test}"
    )


# ---------------------------------------------------------------------------
# Fixtures de escopo de sessão — criadas uma única vez por rodada de testes
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Cria um loop de eventos para a sessão de testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def async_engine_test():
    """Engine assíncrona conectada ao banco de testes."""
    engine = create_async_engine(_get_test_db_url())
    yield engine


@pytest.fixture(scope="session", autouse=True)
async def create_tables(async_engine_test):
    """Cria todas as tabelas antes da suíte e as dropa ao final."""
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Fixtures de escopo de função — recriadas a cada teste
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_db_session(async_engine_test):
    """
    Sessão transacional assíncrona com rollback automático.
    """
    async with async_engine_test.connect() as connection:
        # 2. Iniciamos a transação na conexão
        transaction = await connection.begin()

        # 3. Criamos a sessão vinculada à conexão
        async_session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",  # Opcional: ajuda em sub-transações
        )

        yield async_session

        # --- Limpeza (Ordem Crítica) ---
        # 4. Primeiro, fechamos a sessão para garantir que ela não tente usar a conexão depois
        await async_session.close()

        # 5. Depois, damos o rollback na transação da conexão
        if transaction.is_active:
            await transaction.rollback()


from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
async def _inject_session_into_factories(async_db_session: AsyncSession):
    """Injeta a sessão de teste em TODAS as Factories SQLAlchemy do projeto."""
    for factory_cls in SQLALCHEMY_FACTORIES:
        factory_cls._meta.sqlalchemy_session = async_db_session
    yield
    for factory_cls in SQLALCHEMY_FACTORIES:
        factory_cls._meta.sqlalchemy_session = None


@pytest.fixture
async def client(async_db_session: AsyncSession):
    """
    AsyncClient com `get_db` substituído pela sessão de teste assíncrona.
    """

    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db
    # Usamos ASGITransport para conectar o AsyncClient diretamente à app FastAPI
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_as():
    """Autentica o `client` como um usuário específico para o teste."""

    def _apply(user: models.Users, scopes: list[str] | None = None):
        user_scopes = scopes or ["user"]

        async def override_payload(security_scopes: SecurityScopes):
            required_scopes = security_scopes.scopes

            if required_scopes and not any(
                scope in user_scopes for scope in required_scopes
            ):
                raise error.CustomException(
                    status_code=401,
                    detail="Desculpe, você não tem permissão.",
                )

            return {"sub": str(user.id), "scopes": user_scopes}

        app.dependency_overrides[get_current_payload] = override_payload
        return user

    yield _apply
    app.dependency_overrides.pop(get_current_payload, None)
