from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base_schema import MetaData

__all__ = [
    "GetUserRoles",
    "PatchUserRoles",
    "PostUserRoles",
    "ResponseUserRoles",
]


class PostUserRoles(BaseModel):
    """
    Schema para vincular um papel (role) a um usuário.

    Attributes:
        user_id (UUID): Identificador único do usuário.
        role_id (UUID): Identificador único do papel.
    """

    user_id: UUID = Field(..., description="ID do usuário (UUID)")
    role_id: UUID = Field(..., description="ID do papel (UUID)")


class GetUserRoles(BaseModel):
    """
    Schema para representação do vínculo entre usuário e papel.

    Attributes:
        user_id (UUID): Identificador único do usuário.
        role_id (UUID): Identificador único do papel.
        id (UUID): Identificador único da associação.
    """

    id: UUID = Field(..., description="ID da associação (UUID)")
    user_id: UUID = Field(..., description="ID do usuário")
    role_id: UUID = Field(..., description="ID do papel")

    model_config = ConfigDict(from_attributes=True)


class PatchUserRoles(BaseModel):
    """
    Schema para atualização parcial do vínculo usuário-papel.

    Attributes:
        user_id (UUID | None): Novo ID do usuário.
        role_id (UUID | None): Novo ID do papel.
    """

    user_id: UUID | None = Field(None, description="Novo ID do usuário")
    role_id: UUID | None = Field(None, description="Novo ID do papel")


class ResponseUserRoles(BaseModel):
    meta: MetaData
    data: list[GetUserRoles]

    model_config = ConfigDict(from_attributes=True)
