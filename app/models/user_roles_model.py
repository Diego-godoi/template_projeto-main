from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .roles_model import Roles
    from .users_model import Users


class UserRoles(Base):
    """
    Modelo de associação (tabela intermediária) entre Usuários e Papéis (Roles).

    Attributes:
        user_id (UUID): Identificador único do usuário.
        role_id (UUID): Identificador único do papel.
        user (Users): Objeto do usuário associado.
        role (Roles): Objeto do papel associado.
    """

    user_id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped[Users] = relationship(
        "Users", back_populates="user_roles", passive_deletes=True
    )
    role: Mapped[Roles] = relationship(
        "Roles",
        back_populates="user_roles",
        lazy="noload",
        passive_deletes=True,
    )
