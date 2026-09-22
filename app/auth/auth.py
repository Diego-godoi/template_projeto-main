from __future__ import annotations

import datetime
from collections.abc import Callable

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import error, models
from app.core.config import settings
from app.db.session import get_db

__all__ = [
    "decode_token",
    "encode_token",
    "get_current_payload",
    "require_roles",
]


def _build_token_url() -> str:
    if settings.URL_TOKEN:
        return settings.URL_TOKEN
    prefix = (settings.API_URL_PREFIX or "").rstrip("/")
    return f"{prefix}/login/access-token" if prefix else "/login/access-token"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=_build_token_url())


def encode_token(sub_data: dict | str, exp: float | None = None) -> str:
    exp = settings.ACCESS_TOKEN_EXPIRE_MINUTES if exp is None else exp
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    user_id = (
        sub_data.get("sub") or sub_data.get("user_id")
        if isinstance(sub_data, dict)
        else sub_data
    )
    roles = sub_data.get("roles", []) if isinstance(sub_data, dict) else []
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=exp),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


async def _get_user_with_roles(
    user_id: str, db: AsyncSession
) -> tuple[models.Users, list[str]]:
    """Busca o usuário e os nomes dos papéis em uma única consulta.

    Em um modelo relacional normalizado, `user_roles` é necessária para
    representar a associação N:N. O ganho vem de selecionar apenas os campos
    necessários, em vez de carregar a árvore ORM de relacionamentos.
    """
    stmt = (
        select(models.Users, models.Roles.name)
        .outerjoin(
            models.UserRoles, models.UserRoles.user_id == models.Users.id
        )
        .outerjoin(models.Roles, models.Roles.id == models.UserRoles.role_id)
        .where(models.Users.id == user_id)
    )
    try:
        rows = (await db.execute(stmt)).all()
    except (ValueError, TypeError):
        raise error.CustomException(401, "Usuário não encontrado ou inativo.")
    if not rows or rows[0][0].is_deleted:
        raise error.CustomException(401, "Usuário não encontrado ou inativo.")
    user = rows[0][0]
    roles = sorted({role_name.lower() for _, role_name in rows if role_name})
    return user, roles


async def decode_token(token: str, db: AsyncSession) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise error.CustomException(
                401, "Token inválido: sujeito ausente."
            )
        _, roles = await _get_user_with_roles(user_id, db)
        payload["roles"] = roles
        return payload
    except error.CustomException:
        raise
    except jwt.ExpiredSignatureError:
        raise error.CustomException(401, "Desculpe, o token expirou.")
    except jwt.InvalidTokenError as exc:
        raise error.CustomException(
            401, f"Desculpe, o token é inválido: {exc!s}"
        )
    except Exception:  # noqa: BLE001 - hide internal authentication details
        raise error.CustomException(500, "Erro interno de autenticação")


async def get_current_payload(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await decode_token(token, db)


def require_roles(*required_roles: str) -> Callable:
    expected = {role.lower() for role in required_roles}

    async def dependency(payload: dict = Depends(get_current_payload)) -> dict:
        assigned = {role.lower() for role in payload.get("roles", [])}
        if expected.isdisjoint(assigned):
            raise error.CustomException(
                403, "Acesso negado: você não possui um papel autorizado."
            )
        return payload

    return dependency
