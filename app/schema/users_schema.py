from uuid import UUID

from fastapi import Form
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
        email (Email): Endereço de e-mail único do usuário.
        password (Password): Senha do usuário (será criptografada).
        active (bool | None): Define se o usuário inicia ativo.
        name (str | None): Nome completo do usuário.
        cpf (str): Cadastro de Pessoa Física único.
    """

    # username: str = Field(..., description="Nome de usuário")
    email: Email = Field(..., description="Email do usuário")
    password: Password = Field(..., description="Senha do usuário")
    active: bool | None = Field(
        None, description="Indica se o usuário está ativo"
    )
    name: FullName | None = Field(None, description="Nome completo do usuário")
    cpf: Cpf = Field(..., description="CPF do usuário")

    @classmethod
    def as_form(
        cls,
        email: Email = Form(..., description="Email do usuário"),
        password: Password = Form(..., description="Senha do usuário"),
        active: bool | None = Form(
            None, description="Indica se o usuário está ativo na plataforma"
        ),
        name: FullName = Form(..., description="Nome completo do usuário"),
        cpf: Cpf = Form(..., description="CPF do usuário"),
    ):
        return cls(
            email=email,
            password=password,
            active=active,
            name=name,
            cpf=cpf,
        )


class GetUsers(BaseModel):
    """
    Schema para representação detalhada de um usuário em respostas de leitura.

    Attributes:
        email (str): Endereço de e-mail do usuário.
        active (bool): Status de ativação da conta.
        id (UUID): Identificador único do usuário.
        name (str | None): Nome completo do usuário.
        cpf (str): Cadastro de Pessoa Física único.
    """

    # username: str = Field(..., description="Nome de usuário")
    email: str = Field(..., description="Email do usuário")
    active: bool = Field(..., description="Indica se o usuário está ativo")
    id: UUID = Field(..., description="UUID do usuário")
    name: FullName | None = Field(None, description="Nome completo do usuário")
    cpf: str = Field(..., description="CPF do usuário")

    model_config = ConfigDict(from_attributes=True)


class PatchUsers(BaseModel):
    """
    Schema para atualização parcial dos dados de um usuário.

    Attributes:
        email (str | None): Novo endereço de e-mail.
        password (str | None): Nova senha.
        active (bool | None): Alterar status de ativação.
        name (str | None): Nome completo atualizado.
        cpf (str | None): CPF atualizado.
    """

    # username: str = Field(None, description="Nome de usuário")
    email: Email = Field(None, description="Email do usuário")
    password: Password = Field(None, description="Senha do usuário")
    active: bool | None = Field(
        None, description="Indica se o usuário está ativo"
    )
    name: FullName | None = Field(None, description="Nome completo do usuário")
    cpf: str | None = Field(None, description="CPF do usuário")

    @classmethod
    def as_form(
        cls,
        email: Email | None = Form(None, description="Email do usuário"),
        password: Password | None = Form(None, description="Senha do usuário"),
        name: FullName | None = Form(
            None, description="Nome completo do usuário"
        ),
        cpf: str | None = Form(None, description="CPF do usuário"),
        active: str | None = Form(None, description="Status de ativação"),
    ):
        data = {
            "email": email,
            "password": password,
            "name": name,
            "cpf": cpf,
            "active": active,
        }

        if active is not None and active != "":
            # Converte a string do form ("true", "false", "1", "0") para bool real
            data["active"] = active.lower() in ("true", "1", "t")

        # Remove campos não enviados, pra simular exclude_unset em multipart
        clean_data = {
            k: v for k, v in data.items() if v is not None and v != ""
        }

        return cls(**clean_data)


class ResponseUsers(BaseModel):
    """Modelo para a resposta com a lista de usuários.

    Attributes:
        meta (MetaData): Metadados da resposta.
        data (list[GetUsers]): Lista de usuários.
    """

    meta: MetaData
    data: list[GetUsers]

    model_config = ConfigDict(from_attributes=True)
