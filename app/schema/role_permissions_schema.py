from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base_schema import MetaData

__all__ = [
    "GetRolePermissions",
    "PatchRolePermissions",
    "PostRolePermissions",
    "ResponseRolePermissions",
]


class PostRolePermissions(BaseModel):
    """
    Schema para criação de uma associação entre papel (role) e permissão.

    Attributes:
        role_id (UUID): UUID do papel (role).
        permission_id (UUID): UUID da permissão.
    """

    role_id: UUID = Field(..., description="UUID do papel (role)")
    permission_id: UUID = Field(..., description="UUID da permissão")


class GetRolePermissions(BaseModel):
    """
    Schema para leitura de uma associação role-permissão.

    Attributes:
        id (UUID): Identificador único da associação.
        role_id (UUID): UUID do papel.
        permission_id (UUID): UUID da permissão.
    """

    id: UUID = Field(..., description="Identificador único da associação")
    role_id: UUID = Field(..., description="UUID do papel")
    permission_id: UUID = Field(..., description="UUID da permissão")

    model_config = ConfigDict(from_attributes=True)


class PatchRolePermissions(BaseModel):
    """
    Schema para atualização de uma associação entre papel (role) e permissão.

    Attributes:
        role_id (UUID): UUID do papel (role).
        permission_id (UUID): UUID da permissão.
    """

    role_id: UUID = Field(..., description="UUID do papel (role)")
    permission_id: UUID = Field(..., description="UUID da permissão")


class ResponseRolePermissions(BaseModel):
    """
    Schema para resposta de listagem de associações role-permissão.

    Attributes:
        meta (MetaData): Metadados de paginação.
        data (list[GetRolePermissions]): Lista de associações.
    """

    meta: MetaData
    data: list[GetRolePermissions]

    model_config = ConfigDict(from_attributes=True)
