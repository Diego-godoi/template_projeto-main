from app.core.config import Settings


def test_get_db_urls():
    # Cria uma instância isolada de Settings para não interferir com o ambiente atual
    settings = Settings(
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password!@#",
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT="5433",
        POSTGRES_DB="test_db",
    )

    # Verifica get_async_db_url
    async_url = settings.get_async_db_url()
    assert (
        async_url
        == "postgresql+asyncpg://test_user:test_password%21%40%23@localhost:5433/test_db"
    )

    # Verifica get_db_url
    sync_url = settings.get_db_url()
    assert (
        sync_url
        == "postgresql+psycopg2://test_user:test_password%21%40%23@localhost:5433/test_db"
    )
