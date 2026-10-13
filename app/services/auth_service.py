import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app import core, error, models, schema, util
from app.db import _db

logger = logging.getLogger(__name__)


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

        Os papéis do usuário são incluídos no token e recalculados pelo
        `decode_token()` com base no banco em toda requisição.
        """
        if not username:
            logger.warning("Tentativa de login sem identificador")
            raise error.CustomException(400, "Email ou Senha invalidos")

        stmt = (
            select(models.Users, models.Roles.name)
            .outerjoin(
                models.UserRoles,
                models.UserRoles.user_id == models.Users.id,
            )
            .outerjoin(
                models.Roles,
                models.Roles.id == models.UserRoles.role_id,
            )
            .where(
                models.Users.email == username,
                models.Users.is_deleted == False,
            )
        )
        rows = (await session.execute(stmt)).all()
        user: models.Users | None = rows[0][0] if rows else None

        if not user or not await core.verify_password(password, user.password):
            logger.warning(
                "Tentativa de login rejeitada por credenciais inválidas"
            )
            raise error.CustomException(400, "Email ou Senha invalidos")

        roles = sorted({role.lower() for _, role in rows if role})
        payload_data = {
            "sub": str(user.id),
            "roles": roles,
        }

        logger.info("Login realizado com sucesso")
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

        stmt = (
            select(models.Users)
            .where(
                models.Users.email == email, models.Users.is_deleted == False
            )
            .limit(1)
        )
        user = (await session.execute(stmt)).scalars().first()
        if not user:
            logger.debug(
                "Solicitação de redefinição sem usuário correspondente"
            )
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

        logger.info("Código de redefinição de senha gerado com sucesso")
        return message, (email, core.settings.PROJECT_NAME, body)

    @staticmethod
    async def reset_password(data: schema.ResetPassword, session: _db) -> str:
        """Valida o código e altera a senha do usuário."""
        data.code = util.normalize_uper(data.code)
        stmt = (
            select(models.Users)
            .where(
                models.Users.email == data.email,
                models.Users.is_deleted == False,
            )
            .limit(1)
        )
        user = (await session.execute(stmt)).scalars().first()

        if (
            not user
            or not user.reset_password_code
            or not user.reset_password_expiration
        ):
            logger.warning("Tentativa de redefinição com dados inválidos")
            raise error.CustomException(401, "Email ou código inválido")

        if datetime.now(timezone.utc) > user.reset_password_expiration:
            logger.warning("Tentativa de redefinição com código expirado")
            raise error.CustomException(401, "Código expirado")

        if not await core.verify_password(data.code, user.reset_password_code):
            logger.warning("Tentativa de redefinição com código inválido")
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

        logger.info("Senha redefinida com sucesso")
        return "Senha alterada"
