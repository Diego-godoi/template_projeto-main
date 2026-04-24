from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, Field, model_validator, ConfigDict

from app import util
from app.error import ValidationException

from .base_schema import MetaData
from .types_annotated import Cpf, Email, FullName, Password

__all__ = [
    "PostUsers",
    "GetUsers",
    "PatchUsers",
    "ResponseUsers",
]


class PostUsers(BaseModel):
    """
    Schema para criação de novos usuários no sistema.

    Attributes:
        email (Email): Endereço de e-mail único do usuário.
        password (Password): Senha do usuário (será criptografada).
        active (bool | None): Define se o usuário inicia ativo.
        full_name (str | None): Nome completo do usuário.
        cpf (str): Cadastro de Pessoa Física único.
    """

    # username: str = Field(..., description="Nome de usuário")
    email: str = Field(..., description="Email do usuário")
    password: bytes = Field(..., description="Senha do usuário")
    active: bool | None = Field(None, description="Indica se o usuário está ativo")
    full_name: str | None = Field(None, description="Nome completo do usuário")
    cpf: Cpf = Field(..., description="CPF do usuário")

    @model_validator(mode="before")
    @classmethod
    def validators_user(cls, data) -> "PostUsers":
        errors = []

        try:
            data["email"] = util.normalize_email(data["email"])
        except Exception as e:
            errors.append(
                {
                    "loc": ["body", "email"],
                    "msg": e.detail if hasattr(e, "detail") else str(e),
                    "type": "value_error",
                }
            )

        if "full_name" in data:
            try:
                data["full_name"] = util.normalize_capitalize(data["full_name"])
            except Exception as e:
                errors.append(
                    {
                        "loc": ["body", "full_name"],
                        "msg": e.detail if hasattr(e, "detail") else str(e),
                        "type": "value_error",
                    }
                )

        try:
            data["password"] = util.normalize_password(data["password"])
        except Exception as e:
            errors.append(
                {
                    "loc": ["body", "password"],
                    "msg": e.detail if hasattr(e, "detail") else str(e),
                    "type": "value_error",
                }
            )

        try:
            data["cpf"] = util.validate_cpf(data["cpf"])
        except Exception as e:
            errors.append(
                {
                    "loc": ["body", "cpf"],
                    "msg": e.detail if hasattr(e, "detail") else str(e),
                    "type": "value_error",
                }
            )

        if errors:
            raise ValidationException(errors)

        return data

    @classmethod
    def as_form(
        cls,
        # username: str = Form(..., description="Nome de usuário"),
        email: Email = Form(..., description="Email do usuário"),
        password: Password = Form(..., description="Senha do usuário"),
        active: bool = Form(None, description="Indica se o usuário está ativo"),
        full_name: FullName = Form(None, description="Nome completo do usuário"),
        cpf: Cpf = Form(..., description="CPF do usuário"),
    ):
        return cls(
            # username=username,
            email=email,
            password=password,
            active=active,
            full_name=full_name,
            cpf=cpf,
        )


class GetUsers(BaseModel):
    """
    Schema para representação detalhada de um usuário em respostas de leitura.

    Attributes:
        email (str): Endereço de e-mail do usuário.
        active (bool): Status de ativação da conta.
        id (UUID): Identificador único do usuário.
        full_name (str | None): Nome completo do usuário.
        cpf (str): Cadastro de Pessoa Física único.
    """

    # username: str = Field(..., description="Nome de usuário")
    email: str = Field(..., description="Email do usuário")
    active: bool = Field(..., description="Indica se o usuário está ativo")
    id: UUID = Field(..., description="UUID do usuário")
    full_name: FullName | None = Field(None, description="Nome completo do usuário")
    cpf: str = Field(..., description="CPF do usuário")

    model_config = ConfigDict(from_attributes=True)


class PatchUsers(BaseModel):
    """
    Schema para atualização parcial dos dados de um usuário.

    Attributes:
        email (str | None): Novo endereço de e-mail.
        password (str | None): Nova senha.
        active (bool | None): Alterar status de ativação.
        full_name (str | None): Nome completo atualizado.
        cpf (str | None): CPF atualizado.
    """

    # username: str = Field(None, description="Nome de usuário")
    email: str = Field(None, description="Email do usuário")
    password: bytes = Field(None, description="Senha do usuário")
    active: bool | None = Field(None, description="Indica se o usuário está ativo")
    full_name: str | None = Field(None, description="Nome completo do usuário")
    cpf: str | None = Field(None, description="CPF do usuário")

    @model_validator(mode="before")
    @classmethod
    def validators_user(cls, data) -> "PatchUsers":
        errors = []

        if "email" in data:
            try:
                data["email"] = util.normalize_email(data["email"])
            except Exception as e:
                errors.append(
                    {
                        "loc": ["body", "email"],
                        "msg": e.detail if hasattr(e, "detail") else str(e),
                        "type": "value_error",
                    }
                )

        if "password" in data:
            try:
                data["password"] = util.normalize_password(data["password"])
            except Exception as e:
                errors.append(
                    {
                        "loc": ["body", "password"],
                        "msg": e.detail if hasattr(e, "detail") else str(e),
                        "type": "value_error",
                    }
                )

        if "full_name" in data:
            try:
                data["full_name"] = util.normalize_capitalize(data["full_name"])
            except Exception as e:
                errors.append(
                    {
                        "loc": ["body", "full_name"],
                        "msg": e.detail if hasattr(e, "detail") else str(e),
                        "type": "value_error",
                    }
                )

        if "cpf" in data:
            try:
                data["cpf"] = util.validate_cpf(data["cpf"])
            except Exception as e:
                errors.append(
                    {
                        "loc": ["body", "cpf"],
                        "msg": e.detail if hasattr(e, "detail") else str(e),
                        "type": "value_error",
                    }
                )

        if errors:
            raise ValidationException(errors)

        return data


class ResponseUsers(BaseModel):
    """Modelo para a resposta com a lista de usuários.

    Attributes:
        meta (MetaData): Metadados da resposta.
        data (list[GetUsers]): Lista de usuários.
    """

    meta: MetaData
    data: list[GetUsers]

    model_config = ConfigDict(from_attributes=True)
