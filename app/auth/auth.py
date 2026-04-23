import datetime
import json
from typing import Union

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.orm import Session

from app import error, models
from app.core.config import settings
from app.db.session import get_db

__all__ = [
    "encode_token",
    "decode_token",
    "get_current_payload",
]

SCOPES_DESCRIPTION: dict[str, str] = {
    "user": "Usuário comum",
    "manager": "Gestor",
    "admin": "Administrador",
}


def _build_token_url() -> str:
    """
    Define a URL do endpoint de obtenção de token (para documentação/OpenAPI).

    Se `settings.URL_TOKEN` estiver definido, ele é respeitado.
    Caso contrário, calcula automaticamente usando `API_URL_PREFIX`.
    """
    if settings.URL_TOKEN:
        return settings.URL_TOKEN

    prefix = (settings.API_URL_PREFIX or "").rstrip("/")
    return f"{prefix}/login/access-token" if prefix else "/login/access-token"


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=_build_token_url(),
    scopes=SCOPES_DESCRIPTION,
)


def encode_token(sub, exp: Union[int, float, None] = None) -> str:
    """Codifica um token JWT."""
    try:
        if exp is None:
            exp = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        payload = {
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(minutes=exp),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "sub": sub,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    except Exception as e:
        raise error.custom_HTTPException(e)


def _get_user_from_sub(sub: dict, db: Session) -> models.Users:
    user_id = sub.get("user_id")
    if not user_id:
        raise error.CustomException(
            status_code=401, detail="Desculpe, você não tem permissão."
        )
    user = models.Users.get(db, "id", user_id)
    if not user:
        raise error.CustomException(
            status_code=401, detail="Desculpe, usuário não encontrado."
        )
    if not user.active:
        raise error.CustomException(
            status_code=401, detail="Desculpe, usuário desativado ou excluído."
        )
    return user


def decode_token(
    token: str,
    db: Session,
    scopes: list[str] | None = None,
) -> dict:
    """
    Decodifica JWT e valida scopes.

    Importante: scopes são recalculados dinamicamente via BD em toda request.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        raw_sub = payload.get("sub")
        if isinstance(raw_sub, str):
            sub = json.loads(raw_sub)
        else:
            sub = raw_sub

        if not isinstance(sub, dict):
            raise error.CustomException(401, "Desculpe, o token é inválido.")

        user = _get_user_from_sub(sub, db)
        role_names = [
            ur.role.name
            for ur in (user.user_roles or [])
            if getattr(ur, "role", None) is not None
            and getattr(ur.role, "name", None) is not None
        ]
        sub["scopes"] = role_names

        if scopes:
            token_scopes = sub.get("scopes", [])
            if not isinstance(token_scopes, list):
                token_scopes = []
            if any(scope not in token_scopes for scope in scopes):
                raise error.CustomException(401, "Desculpe, você não tem permissão.")
        return sub
    except jwt.ExpiredSignatureError:
        raise error.CustomException(401, "Desculpe, o token expirou.")
    except jwt.InvalidTokenError:
        raise error.CustomException(401, "Desculpe, o token é inválido.")
    except Exception as e:
        raise error.custom_HTTPException(e)


async def get_current_payload(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Dependency genérica que valida JWT e aplica scopes (OAuth2)."""
    try:
        return decode_token(token, db, scopes=list(security_scopes.scopes))
    except Exception as e:
        raise error.custom_HTTPException(e)
