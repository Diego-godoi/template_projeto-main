# tests/conftest.py
"""
Infraestrutura base de testes (Épico 5.1).

Estratégia de isolamento:
- Engine aponta para banco `template_teste` (banco dedicado para testes).
- Cada teste roda dentro de uma transação que sofre ROLLBACK ao final,
  garantindo que nenhum dado persista entre os testes.
- O FastAPI TestClient recebe override de `get_db` para usar a sessão de teste.
"""

from urllib.parse import quote_plus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app

# ---------------------------------------------------------------------------
# URL do banco de teste
# ---------------------------------------------------------------------------


def _get_test_db_url() -> str:
    user = quote_plus(settings.POSTGRES_USER)
    password = quote_plus(settings.POSTGRES_PASSWORD)
    db_test = settings.POSTGRES_DB_TEST  # lê do .env
    return (
        f"postgresql+psycopg2://{user}:{password}@"
        f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{db_test}"
    )


# ---------------------------------------------------------------------------
# Fixtures de escopo de sessão — criadas uma única vez por rodada de testes
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine_test():
    """Engine conectada ao banco de testes."""
    engine = create_engine(_get_test_db_url())
    yield engine
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def create_tables(engine_test):
    """Cria todas as tabelas antes da suíte e as dropa ao final."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


# ---------------------------------------------------------------------------
# Fixtures de escopo de função — recriadas a cada teste
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session(engine_test):
    """
    Sessão transacional com rollback automático.

    Abre uma conexão → inicia transação → cria savepoint → executa teste
    → faz rollback para o savepoint → fecha tudo.
    Resultado: banco limpo após cada teste, sem delete explícito.
    """
    connection = engine_test.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()

    # Habilita savepoints para que o rollback funcione mesmo com commits internos
    session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session):
    """
    TestClient com `get_db` substituído pela sessão de teste.

    Garante que os endpoints usem a mesma sessão transacional controlada
    pelos testes, sem nunca tocar o banco de produção/dev.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # teardown gerenciado pela fixture db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
