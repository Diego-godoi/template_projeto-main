from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, Field, model_validator

from app import error, models

from .base_schema import MetaData
from .types_annotated import *

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
        try:
            if "name" not in data:
                raise error.CustomException(
                    422,
                    "É necessário informar o name para prosseguir.",
                )
            ...
            return data
        except Exception as e:
            raise error.custom_HTTPException(e)

    @classmethod
    def as_form(
        cls,
        name: str = Form(..., description="name Documentar"),
        access_level: int = Form(..., description="access_level Documentar"),
        description: str
        | None = Form(None, description="description Documentar"),
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

    class Config:
        from_attributes = True


class PatchRoles(BaseModel):
    """
    Schema para atualização parcial de um papel.

    Attributes:
        name (str | None): Novo nome do papel.
        access_level (int | None): Novo nível de acesso.
        description (str | None): Nova descrição.
    """

    name: str = Field(None, description="Novo nome do papel")
    access_level: int = Field(None, description="Novo nível de acesso")
    description: str | None = Field(None, description="Nova descrição")


class ResponseRoles(BaseModel):
    meta: MetaData
    data: list[GetRoles]

    class Config:
        from_attributes = True
