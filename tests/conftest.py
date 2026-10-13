# tests/conftest.py
"""
Infraestrutura base de testes (Épico 5.1).
"""

import asyncio
from urllib.parse import quote_plus

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from app import models
from app.auth import get_current_payload
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app
from tests.factories import SQLALCHEMY_FACTORIES


def _get_test_db_url() -> str:
    user = quote_plus(settings.POSTGRES_USER)
    password = quote_plus(settings.POSTGRES_PASSWORD)
    db_test = settings.POSTGRES_DB_TEST
    return (
        f"postgresql+asyncpg://{user}:{password}@"
        f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT_TEST}/{db_test}"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Cria um loop de eventos para a sessão de testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine_test():
    """Engine assíncrona conectada ao banco de testes."""
    engine = create_async_engine(_get_test_db_url())
    yield engine
    # Libera o pool de conexões ao finalizar os testes
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def create_tables(async_engine_test):
    """Cria todas as tabelas antes da suíte e as dropa ao final."""
    async with async_engine_test.begin() as conn:
        # Drop before create para limpar sujeira de testes cancelados pela metade

        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_db_session(async_engine_test):
    """
    Sessão transacional assíncrona com rollback automático.
    """
    async with async_engine_test.connect() as connection:
        transaction = await connection.begin()

        async_session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield async_session

        # Limpeza: Apenas fecha a sessão e dá rollback na transação pai.
        await async_session.close()
        if transaction.is_active:
            await transaction.rollback()


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
    """AsyncClient com `get_db` substituído pela sessão de teste assíncrona."""

    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Remove apenas o override injetado por esta fixture
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_as():
    """Autentica o client com um papel RBAC clássico."""

    def _apply(
        user: models.Users,
        role: str | models.StandardRoles = models.StandardRoles.USER,
    ):
        role_name = getattr(role, "value", role)

        async def override_payload():
            return {"sub": str(user.id), "roles": [role_name]}

        app.dependency_overrides[get_current_payload] = override_payload
        return user

    yield _apply
    app.dependency_overrides.pop(get_current_payload, None)
