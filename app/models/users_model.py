from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, LargeBinary, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user_roles_model import UserRoles


class Users(Base):
    """
    Modelo representativo da tabela de usuários do sistema.

    Attributes:
        name (str): Nome completo do usuário.
        email (str): Endereço de e-mail único usado para autenticação.
        cpf (str): Cadastro de Pessoa Física único (apenas números).
        password (bytes): Hash da senha criptografada.
        is_deleted (bool): soft delete (default: False).
        reset_password_code (str | None): Código temporário para redefinição de senha.
        reset_password_expiration (datetime | None): Prazo de validade do código de redefinição.
        user_roles (list[UserRoles]): Lista de associações de papéis vinculadas ao usuário.
    """

    __table_args__ = (
        Index(
            "uq_users_email_not_deleted",
            "email",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "uq_users_cpf_not_deleted",
            "cpf",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )

    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    cpf: Mapped[str] = mapped_column(String(11))
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    reset_password_code: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    reset_password_expiration: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user_roles: Mapped[list[UserRoles]] = relationship(
        "UserRoles",
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
