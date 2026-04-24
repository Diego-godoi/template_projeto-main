from email import errors
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app import error, util

from .base_schema import MetaData

__all__ = [
    "PostRoles",
    "GetRoles",
    "PatchRoles",
    "ResponseRoles",
]


class PostRoles(BaseModel):
    """
    Schema para criação de novos papéis (roles) no sistema.

    Attributes:
        name (str): Nome identificador do papel.
        access_level (int): Nível de permissão associado.
        description (str | None): Descrição opcional das permissões.
    """

    name: str = Field(..., description="Nome único do papel (ex: 'admin')")
    access_level: int = Field(..., description="Nível numérico de acesso")
    description: str | None = Field(
        None, description="Descrição detalhada das responsabilidades"
    )

    @model_validator(mode="before")
    @classmethod
    def validators_roles(self, data) -> "PostRoles":
        errors =[]
        try:
            data["name"] = util.normalize_capitalize(data["name"])
        except Exception as e:
             errors.append(
                {
                    "loc": ["body", "name"],
                    "msg": e.detail if hasattr(e, "detail") else str(e),
                    "type": "value_error",
                }
            )

        if errors:
            raise error.ValidationException(errors)

        return data

    @classmethod
    def as_form(
        cls,
        name: str = Form(..., description="Nome do papel"),
        access_level: int = Form(..., description="Nível numérico de acesso"),
         description: str | None = Form(None, description="Descrição detalhada das responsabilidades"),
    ):
        return cls(
            name=name,
            access_level=access_level,
            description=description,
        )


class GetRoles(BaseModel):
    """
    Schema para representação de um papel em respostas de leitura.

    Attributes:
        name (str): Nome do papel.
        access_level (int): Nível de permissão.
        description (str | None): Descrição do papel.
        id (UUID): Identificador único do papel.
    """

    name: str = Field(..., description="Nome do papel")
    access_level: int = Field(..., description="Nível de acesso")
    description: str | None = Field(None, description="Descrição do papel")
    id: UUID = Field(..., description="Identificador único (UUID)")

    model_config = ConfigDict(from_attributes=True)


class PatchRoles(BaseModel):
    """
    Schema para atualização parcial de um papel.

    Attributes:
        name (str | None): Novo nome do papel.
        access_level (int | None): Novo nível de acesso.
        description (str | None): Nova descrição.
    """

    name: str | None = Field(None, description="Novo nome do papel")
    access_level: int | None = Field(None, description="Novo nível de acesso")
    description: str | None = Field(None, description="Nova descrição")


class ResponseRoles(BaseModel):
    meta: MetaData
    data: list[GetRoles]

    model_config = ConfigDict(from_attributes=True)
