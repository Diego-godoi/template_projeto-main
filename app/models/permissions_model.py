from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .role_permissions_model import RolePermissions


class Permissions(Base):
    """
    Modelo representativo das permissões do sistema.

    Attributes:
        name (str): Nome único da permissão no formato 'verbo:modulo' (ex: 'read:users').
        module (str): Módulo ao qual a permissão pertence (ex: 'users', 'roles').
        role_permissions (list[RolePermissions]): Associações com papéis (roles).
    """

    name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)

    role_permissions: Mapped[list[RolePermissions]] = relationship(
        "RolePermissions",
        back_populates="permission",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
