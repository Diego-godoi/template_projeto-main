from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import core, error, models, schema, util
from app.db import _db
from app.util import normalize_lower


class AuthService:
    """
    Camada de serviço para autenticação.
    """

    @staticmethod
    async def login(
        username: str, password: str, session: _db
    ) -> tuple[models.Users, dict]:
        """
        Autentica um usuário e retorna (user, sub) para geração de JWT.

        Obs: `sub` contém scopes, mas a autorização é dinâmica porque o
        `decode_token()` recalcula scopes com base no BD em toda request.
        """
        username_normalizado = normalize_lower(username)
        if not username_normalizado:
            raise error.CustomException(400, "Email ou Senha invalidos")

        stmt = (
            select(models.Users)
            .where(models.Users.email == username_normalizado)
            .options(
                selectinload(models.Users.user_roles)
                .selectinload(models.UserRoles.role)
                .selectinload(models.Roles.role_permissions)
                .selectinload(models.RolePermissions.permission)
            )
            .limit(1)
        )
        user: models.Users | None = (
            (await session.execute(stmt)).scalars().first()
        )

        if not user or not await core.verify_password(password, user.password):
            raise error.CustomException(400, "Email ou Senha invalidos")
        if not user.active:
            raise error.CustomException(401, "Usuario Inativo")

        user_permissions = set()
        for ur in user.user_roles or []:
            role = getattr(ur, "role", None)
            if not role:
                continue

            role_perms = getattr(role, "role_permissions", None) or getattr(
                role, "permissions", []
            )
            for item in role_perms:
                perm = getattr(item, "permission", item)
                perm_name = getattr(perm, "name", None)
                if perm_name:
                    user_permissions.add(str(perm_name).lower())

        payload_data = {
            "sub": str(user.id),
            "scopes": list(user_permissions),
        }

        return user, payload_data

    @staticmethod
    async def request_password_reset(
        email: str, session: _db
    ) -> tuple[str, tuple[str, str, str] | None]:
        """
        Gera e persiste um código de redefinição de senha.

        Retorna uma mensagem genérica (anti-enumeração) e, se o usuário existir,
        os parâmetros necessários para envio de e-mail (to, subject, body).
        """
        message = (
            "Se o e-mail estiver cadastrado, as instruções serão enviadas."
        )

        stmt = select(models.Users).where(models.Users.email == email).limit(1)
        user = (await session.execute(stmt)).scalars().first()
        if not user:
            return message, None

        code = util.generate_code()
        body = util.template_string("reset_password.html", {"code": code})

        expiration = datetime.now(timezone.utc) + timedelta(
            minutes=core.settings.RESET_PASSWORD_TOKEN_EXPIRATION_MINUTES
        )

        user.reset_password_code = await core.get_password_hash(code)
        user.reset_password_expiration = expiration

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return message, (email, core.settings.PROJECT_NAME, body)

    @staticmethod
    async def reset_password(data: schema.ResetPassword, session: _db) -> str:
        """Valida o código e altera a senha do usuário."""
        data.code = util.normalize_uper(data.code)
        stmt = (
            select(models.Users)
            .where(models.Users.email == data.email)
            .limit(1)
        )
        user = (await session.execute(stmt)).scalars().first()

        if (
            not user
            or not user.reset_password_code
            or not user.reset_password_expiration
        ):
            raise error.CustomException(401, "Email ou código inválido")

        if datetime.now(timezone.utc) > user.reset_password_expiration:
            raise error.CustomException(401, "Código expirado")

        if not await core.verify_password(data.code, user.reset_password_code):
            raise error.CustomException(401, "Email ou código inválido")

        senha_final = (
            data.password.encode("utf-8")
            if isinstance(data.password, str)
            else data.password
        )

        user.reset_password_code = None
        user.reset_password_expiration = None
        user.password = await core.get_password_hash(senha_final)

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return "Senha alterada"
