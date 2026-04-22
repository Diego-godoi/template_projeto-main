from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, Field, model_validator

from app import error, models

from .base_schema import MetaData

# from .roles_schema import GetRoles


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

    @model_validator(mode="before")
    @classmethod
    def validators_user_roles(self, data) -> "PostUserRoles":
        try:
            return data
        except Exception as e:
            raise error.custom_HTTPException(e)

    @classmethod
    def as_form(
        cls,
        user_id: UUID = Form(..., description="user_id Documentar"),
        role_id: UUID = Form(..., description="role_id Documentar"),
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

    class Config:
        from_attributes = True


class PatchUserRoles(BaseModel):
    """
    Schema para atualização parcial do vínculo usuário-papel.

    Attributes:
        user_id (UUID | None): Novo ID do usuário.
        role_id (UUID | None): Novo ID do papel.
    """

    user_id: UUID = Field(None, description="Novo ID do usuário")
    role_id: UUID = Field(None, description="Novo ID do papel")


class ResponseUserRoles(BaseModel):
    meta: MetaData
    data: list[GetUserRoles]

    class Config:
        from_attributes = True
