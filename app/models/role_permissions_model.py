from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .permissions_model import Permissions
    from .roles_model import Roles


class RolePermissions(Base):
    """
    Modelo de associação (tabela intermediária) entre Papéis (Roles) e Permissões (Permissions).

    Attributes:
        role_id (UUID): Identificador único do papel.
        permission_id (UUID): Identificador único da permissão.
        role (Roles): Objeto do papel associado.
        permission (Permissions): Objeto da permissão associada.
    """

    role_id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[Roles] = relationship(
        "Roles", back_populates="role_permissions", lazy="noload"
    )
    permission: Mapped[Permissions] = relationship(
        "Permissions", back_populates="role_permissions", lazy="noload"
    )
