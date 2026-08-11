from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user_roles_model import UserRoles


class Users(Base):
    """
    Modelo representativo da tabela de usuários do sistema.

    Attributes:
        email (str): Endereço de e-mail único usado para autenticação.
        name (str | None): Nome completo do usuário.
        cpf (str): Cadastro de Pessoa Física único (apenas números).
        password (bytes): Hash da senha criptografada.
        active (bool): Status de ativação da conta (default: True).
        reset_password_code (str | None): Código temporário para redefinição de senha.
        reset_password_expiration (datetime | None): Prazo de validade do código de redefinição.
        user_roles (list[UserRoles]): Lista de associações de papéis vinculadas ao usuário.
    """

    email: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(), nullable=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    reset_password_code: Mapped[bytes] = mapped_column(
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
