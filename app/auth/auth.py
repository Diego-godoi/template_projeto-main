import datetime

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import error, models
from app.core.config import settings
from app.db.init_db import SYSTEM_SCOPES
from app.db.session import get_db

__all__ = [
    "decode_token",
    "encode_token",
    "get_current_payload",
]

SCOPES_DESCRIPTION: dict[str, str] = {
    "user": "Usuário comum",
    "manager": "Gestor",
    "admin": "Administrador",
}


def _build_token_url() -> str:
    """Define a URL do endpoint de obtenção de token (para documentação/OpenAPI)."""
    if settings.URL_TOKEN:
        return settings.URL_TOKEN

    prefix = (settings.API_URL_PREFIX or "").rstrip("/")
    return f"{prefix}/login/access-token" if prefix else "/login/access-token"


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=_build_token_url(),
    scopes=SYSTEM_SCOPES,
)


def encode_token(sub_data: dict | str, exp: float | None = None) -> str:
    """Codifica um token JWT."""
    if exp is None:
        exp = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    now = datetime.datetime.now(tz=datetime.timezone.utc)

    if isinstance(sub_data, dict):
        user_id = sub_data.get("sub") or sub_data.get("user_id")
        scopes = sub_data.get("scopes", [])
    else:
        user_id = sub_data
        scopes = []

    payload = {
        "sub": str(user_id),
        "scopes": scopes,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=exp),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


async def _get_user_from_sub(user_id: str, db: AsyncSession) -> models.Users:
    # Consulta com eager loading encadeado para evitar erros de lazy load assíncrono
    stmt = (
        select(models.Users)
        .where(models.Users.id == user_id)
        .options(
            selectinload(models.Users.user_roles)
            .selectinload(models.UserRoles.role)
            .selectinload(models.Roles.role_permissions)
            .selectinload(models.RolePermissions.permission)
        )
    )

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise error.CustomException(
            status_code=401, detail="Desculpe, usuário não encontrado."
        )
    if not user.active:
        raise error.CustomException(
            status_code=401, detail="Desculpe, usuário desativado ou excluído."
        )
    return user


async def decode_token(
    token: str,
    db: AsyncSession,
    scopes: list[str] | None = None,
) -> dict:
    """
    Decodifica JWT e valida scopes (permissões granulares).

    Importante: scopes são recalculados dinamicamente via BD em toda request.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        if not user_id:
            raise error.CustomException(
                401, "Token inválido: sujeito ausente."
            )

        user = await _get_user_from_sub(user_id, db)

        # Extração das permissões granulares atreladas às roles do usuário
        user_permissions = set()
        for ur in user.user_roles or []:
            role = getattr(ur, "role", None)
            if not role:
                continue

            # Obtém a lista de permissões (seja via pivot 'role_permissions' ou direto 'permissions')
            role_perms = getattr(role, "role_permissions", None) or getattr(
                role, "permissions", []
            )

            for item in role_perms:
                perm = getattr(item, "permission", item)
                perm_name = getattr(perm, "name", None)
                if perm_name:
                    user_permissions.add(str(perm_name).lower())

        current_scopes = list(user_permissions)
        payload["scopes"] = current_scopes

        if scopes and not any(
            scope.lower() in current_scopes for scope in scopes
        ):
            raise error.CustomException(
                403,
                "Acesso negado: você não possui permissão para esta ação.",
            )
        return payload

    except error.CustomException:
        raise
    except jwt.ExpiredSignatureError:
        raise error.CustomException(401, "Desculpe, o token expirou.")
    except jwt.InvalidTokenError as e:
        raise error.CustomException(
            401, f"Desculpe, o token é inválido. Erro interno: {e!s}"
        )
    except Exception:  # noqa: BLE001 — barreira final
        raise error.CustomException(500, "Erro interno de autenticação")


async def get_current_payload(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency genérica que valida JWT e aplica scopes (OAuth2)."""
    return await decode_token(token, db, scopes=list(security_scopes.scopes))
