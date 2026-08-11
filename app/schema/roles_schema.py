from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base_schema import MetaData
from .types_annotated import FullName

__all__ = [
    "GetRoles",
    "PatchRoles",
    "PostRoles",
    "ResponseRoles",
]


class PostRoles(BaseModel):
    """
    Schema para criação de novos papéis (roles) no sistema.

    Attributes:
        name (FullName): Nome identificador do papel.
        description (str | None): Descrição opcional das permissões.
    """

    name: FullName = Field(
        ..., description="Nome único do papel (ex: 'admin')"
    )
    description: str | None = Field(
        None, description="Descrição detalhada das responsabilidades"
    )


class GetRoles(BaseModel):
    """
    Schema para representação de um papel em respostas de leitura.

    Attributes:
        id (UUID): Identificador único do papel.
        name (str): Nome do papel.
        description (str | None): Descrição do papel.
        is_system (bool): Indica se o papel é do sistema.
    """

    id: UUID = Field(..., description="Identificador único (UUID)")
    name: str = Field(..., description="Nome do papel")
    description: str | None = Field(None, description="Descrição do papel")
    is_system: bool = Field(..., description="Indica se o papel é do sistema")

    model_config = ConfigDict(from_attributes=True)


class PatchRoles(BaseModel):
    """
    Schema para atualização parcial de um papel.

    Attributes:
        name (FullName | None): Novo nome do papel.
        description (str | None): Nova descrição.
    """

    name: FullName | None = Field(None, description="Novo nome do papel")
    description: str | None = Field(None, description="Nova descrição")


class ResponseRoles(BaseModel):
    """
    Schema para resposta com a lista de papéis.
    """

    meta: MetaData
    data: list[GetRoles]

    model_config = ConfigDict(from_attributes=True)
