from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base_schema import MetaData
from .types_annotated import PermissionName

__all__ = [
    "GetPermissions",
    "PatchPermissions",
    "PostPermissions",
    "ResponsePermissions",
]


class PostPermissions(BaseModel):
    """
    Schema para criação de uma nova permissão no sistema.

    Attributes:
        name (PermissionName): Nome único da permissão (ex: 'read:users').
        module (str): Módulo ao qual a permissão pertence (ex: 'users').
    """

    name: PermissionName = Field(
        ...,
        max_length=45,
        description="Nome único da permissão (ex: 'read:users')",
    )
    module: str = Field(
        ...,
        max_length=50,
        description="Módulo ao qual a permissão pertence (ex: 'users')",
    )


class GetPermissions(BaseModel):
    """
    Schema para leitura de uma permissão.

    Attributes:
        id (UUID): Identificador único da permissão.
        name (str): Nome da permissão.
        module (str): Módulo da permissão.
    """

    id: UUID = Field(..., description="Identificador único da permissão")
    name: str = Field(..., description="Nome da permissão")
    module: str = Field(..., description="Módulo da permissão")

    model_config = ConfigDict(from_attributes=True)


class PatchPermissions(BaseModel):
    """
    Schema para atualização parcial de uma permissão.

    Attributes:
        name (PermissionName | None): Novo nome da permissão.
        module (str | None): Novo módulo da permissão.
    """

    name: PermissionName | None = Field(
        None, max_length=45, description="Nome da permissão"
    )
    module: str | None = Field(
        None, max_length=50, description="Módulo da permissão"
    )


class ResponsePermissions(BaseModel):
    """
    Schema para resposta de listagem de permissões.

    Attributes:
        meta (MetaData): Metadados de paginação.
        data (list[GetPermissions]): Lista de permissões.
    """

    meta: MetaData
    data: list[GetPermissions]

    model_config = ConfigDict(from_attributes=True)
