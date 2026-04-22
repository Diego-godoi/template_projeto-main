from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user_roles_model import UserRoles


class Roles(Base):
    """
    Modelo representativo dos papéis (roles) e permissões do sistema.

    Attributes:
        name (str): Nome do papel (ex: 'admin', 'user').
        access_level (int): Nível de acesso numérico para controle de permissões.
        description (str | None): Descrição detalhada das responsabilidades do papel.
        user_roles (list[UserRoles]): Lista de associações com usuários.
    """

    name: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    access_level: Mapped[int] = mapped_column(Integer(), nullable=False)
    description: Mapped[str | None] = mapped_column(String(250))

    user_roles: Mapped[list["UserRoles"]] = relationship(
        "UserRoles", back_populates="role"
    )
