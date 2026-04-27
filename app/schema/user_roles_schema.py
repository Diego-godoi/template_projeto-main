from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field

from .base_schema import MetaData

__all__ = [
    "PostUserRoles",
    "GetUserRoles",
    "PatchUserRoles",
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

    @classmethod
    def as_form(
        cls,
        user_id: UUID = Form(..., description="ID do usuário (UUID)"),
        role_id: UUID = Form(..., description="ID do papel (UUID)"),
    ):
        return cls(
            user_id=user_id,
            role_id=role_id,
        )


class GetUserRoles(BaseModel):
    """
    Schema para representação do vínculo entre usuário e papel.

    Attributes:
        user_id (UUID): Identificador único do usuário.
        role_id (UUID): Identificador único do papel.
        id (UUID): Identificador único da associação.
    """

    user_id: UUID = Field(..., description="ID do usuário")
    role_id: UUID = Field(..., description="ID do papel")
    id: UUID = Field(..., description="ID da associação (UUID)")

    #    role: list[GetRoles | None]

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
