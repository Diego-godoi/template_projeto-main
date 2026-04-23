from datetime import datetime, timedelta

from app import auth, core, error, models, schema, util
from app.db import _db


class AuthService:
    """
    Camada de serviço para autenticação.
    """

    @staticmethod
    def login(username: str, password: str, session: _db) -> tuple[models.Users, dict]:
        """
        Autentica um usuário e retorna (user, sub) para geração de JWT.

        Obs: `sub` contém scopes, mas a autorização é dinâmica porque o
        `decode_token()` recalcula scopes com base no BD em toda request.
        """
        username_normalizado = (username or "").strip().lower()
        if not username_normalizado:
            raise error.CustomException(400, "Email ou Senha invalidos")

        user: models.Users | None = models.Users.get(
            _db=session, attribute="email", value=username_normalizado
        )
        if not user or not core.verify_password(password, user.password):
            raise error.CustomException(400, "Email ou Senha invalidos")
        if not user.active:
            raise error.CustomException(401, "Usuario Inativo")

        role_names = [
            ur.role.name
            for ur in (user.user_roles or [])
            if getattr(ur, "role", None) is not None
            and getattr(ur.role, "name", None) is not None
        ]

        sub = {
            "user_id": str(user.id),
            "scopes": role_names
        }

        return user, sub

    @staticmethod
    def request_password_reset(
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

        user = models.Users.get(session, "email", email)
        if not user:
            return message, None

        code = util.generate_code()
        body = util.template_string("reset_password.html", {"code": code})

        expiration = datetime.now() + timedelta(
            minutes=core.settings.RESET_PASSWORD_TOKEN_EXPIRATION_MINUTES
        )

        user.reset_password_code = core.get_password_hash(code)
        user.reset_password_expiration = expiration

        session.add(user)
        session.commit()
        session.refresh(user)

        return message, (email, core.settings.PROJECT_NAME, body)

    @staticmethod
    def reset_password(data: schema.ResetPassword, session: _db) -> str:
        """Valida o código e altera a senha do usuário."""
        data.code = util.normalize_uper(data.code)
        user = models.Users.get(session, "email", data.email)

        if (
            not user
            or not user.reset_password_code
            or not user.reset_password_expiration
        ):
            raise error.CustomException(401, "Email ou código inválido")

        if datetime.now() > user.reset_password_expiration:
            raise error.CustomException(401, "Código expirado")

        if not core.verify_password(data.code, user.reset_password_code):
            raise error.CustomException(401, "Email ou código inválido")

        senha_final = (
            data.password.encode("utf-8")
            if isinstance(data.password, str)
            else data.password
        )

        user.reset_password_code = None
        user.reset_password_expiration = None
        user.password = senha_final

        session.add(user)
        session.commit()
        session.refresh(user)

        return "Senha alterada"
