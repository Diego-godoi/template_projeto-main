from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings

__all__ = ["settings"]


class Settings(BaseSettings):
    API_URL_PREFIX: str | None = Field(None, description="Prefixo da URL da API")
    SECRET_KEY: str | None = Field(
        None,
        description="Chave secreta para criptografia",
    )
    RESET_PASSWORD_TOKEN_EXPIRATION_MINUTES: int | None = Field(
        20, description="Validade do token de redefinição de senha em minutos"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = Field(
        86400, description="Validade do token de acesso em minutos"
    )
    REGISTER_TOKEN_EXPIRE_MINUTES: int | None = Field(
        20, description="Validade do token de registro em minutos"
    )

    PROJECT_VERSION: str | None = Field("1.0", description="Versão do projeto")
    PROJECT_NAME: str | None = Field(None, description="Nome do projeto")
    SMTP_TLS: bool | None = Field(None, description="Utilizar TLS para SMTP")
    SMTP_PORT: int | None = Field(None, description="Porta para conexão SMTP")
    SMTP_HOST: str | None = Field(None, description="Host para conexão SMTP")
    SMTP_PASSWORD: str | None = Field(None, description="Senha para conexão SMTP")

    EMAILS_FROM_EMAIL: str | None = Field(None, description="E-mail do remetente")
    EMAILS_FROM_NAME: str | None = Field(None, description="Nome do remetente")
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int | None = Field(
        48, description="Validade do token de redefinição de e-mail em horas"
    )
    DEBUG: bool = Field(description="Modo de depuração")

    FIRST_SUPERUSER: str | None = Field(
        None, description="Nome de usuário do primeiro superusuário"
    )
    FIRST_SUPERUSER_PASSWORD: str | None = Field(
        None, description="Senha do primeiro superusuário"
    )

    TEMPLATES_DIR: str | None = Field(None, description="Diretório de templates")
    UPLOAD_DIR: str | None = Field(None, description="Diretório de upload")

    URL_TOKEN: str | None = Field(
        None,
        description="URL de login (opcional; default calculado automaticamente)",
    )

    POSTGRES_USER: str = Field(description="Usuário do banco de dados PostgreSQL")
    POSTGRES_PASSWORD: str = Field(description="Senha do banco de dados PostgreSQL")
    POSTGRES_SERVER: str = Field(
        description="Host/Servidor do banco de dados PostgreSQL"
    )
    POSTGRES_PORT: str = Field("5432", description="Porta do banco de dados PostgreSQL")
    POSTGRES_DB: str = Field(description="Nome do banco de dados PostgreSQL")
    POSTGRES_DB_TEST: str = Field(
        "template_teste", description="Nome do banco de dados para testes"
    )

    def get_async_db_url(self) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)

        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_db_url(self) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)

        return (
            f"postgresql+psycopg2://{user}:{password}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
