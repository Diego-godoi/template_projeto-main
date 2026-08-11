from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .role_permissions_model import RolePermissions
    from .user_roles_model import UserRoles


class Roles(Base):
    """
    Modelo representativo dos papéis (roles) do sistema.

    Attributes:
        name (str): Nome do papel (ex: 'Admin', 'User').
        description (str | None): Descrição detalhada das responsabilidades do papel.
        is_system (bool): Indica se é um papel do sistema (imutável).
        user_roles (list[UserRoles]): Lista de associações com usuários.
        role_permissions (list[RolePermissions]): Lista de permissões vinculadas.
    """

    name: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user_roles: Mapped[list[UserRoles]] = relationship(
        "UserRoles",
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    role_permissions: Mapped[list[RolePermissions]] = relationship(
        "RolePermissions",
        back_populates="role",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
