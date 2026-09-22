from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base_schema import MetaData
from .types_annotated import Cpf, Email, FullName, Password

__all__ = [
    "GetUsers",
    "PatchUsers",
    "PostUsers",
    "ResponseUsers",
]


class PostUsers(BaseModel):
    """
    Schema para criação de novos usuários no sistema.

    Attributes:
        name (str): Nome completo do usuário.
        email (Email): Endereço de e-mail único do usuário.
        cpf (str): Cadastro de Pessoa Física único.
        password (Password): Senha do usuário (será criptografada).
    """

    name: FullName = Field(..., description="Nome completo do usuário")
    email: Email = Field(..., description="Email do usuário")
    password: Password = Field(..., description="Senha do usuário")
    cpf: Cpf = Field(..., description="CPF do usuário")


class GetUsers(BaseModel):
    """
    Schema para representação detalhada de um usuário em respostas de leitura.

    Attributes:
        id (UUID): Identificador único do usuário.
        name (str): Nome completo do usuário.
        email (str): Endereço de e-mail do usuário.
        cpf (str): Cadastro de Pessoa Física único.
    """

    id: UUID = Field(..., description="UUID do usuário")
    name: FullName = Field(..., description="Nome completo do usuário")
    email: Email = Field(..., description="Email do usuário")
    cpf: Cpf = Field(..., description="CPF do usuário")

    model_config = ConfigDict(from_attributes=True)


class PatchUsers(BaseModel):
    """
    Schema para atualização parcial dos dados de um usuário.

    Attributes:
        name (str | None): Nome completo atualizado.
        email (str | None): Novo endereço de e-mail.
        cpf (str | None): CPF atualizado.
        password (str | None): Nova senha.
    """

    name: FullName | None = Field(None, description="Nome completo do usuário")
    email: Email | None = Field(None, description="Email do usuário")
    cpf: Cpf | None = Field(None, description="CPF do usuário")
    password: Password | None = Field(None, description="Senha do usuário")


class ResponseUsers(BaseModel):
    """Modelo para a resposta com a lista de usuários.

    Attributes:
        meta (MetaData): Metadados da resposta.
        data (list[GetUsers]): Lista de usuários.
    """

    meta: MetaData
    data: list[GetUsers]

    model_config = ConfigDict(from_attributes=True)
