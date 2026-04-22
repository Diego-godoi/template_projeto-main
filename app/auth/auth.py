import datetime
import json
from typing import Union

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import error, models
from app.core.config import settings
from app.db.session import get_db

__all__ = ["Key", "encode_token", "decode_token"]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.URL_TOKEN)


def encode_token(sub, exp):
    """
    Codifica um token JWT.

    Args:
        sub (Any): O assunto do token.
        exp (Union[int, float]): O tempo de expiração do token em minutos.

    Returns:
        str: O token JWT codificado.
    """
    try:
        payload = {
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(minutes=exp),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "sub": sub,
        }
        result = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return result
    except Exception as e:
        raise error.custom_HTTPException(e)


def get_user_from_payload(payload: dict, db: Session) -> models.Users:
    user_id = payload.get("user_id")
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


def decode_token(
    Authentication: str, db: Session, key: Union[int, None] = None
) -> dict:
    try:
        payload = jwt.decode(
            Authentication, settings.SECRET_KEY, algorithms="HS256"
        )

        if isinstance(payload["sub"], str):
            sub = json.loads(payload["sub"])

        else:
            sub = payload["sub"]

        if "user_id" in sub:
            get_user_from_payload(sub, db)
        if key and key not in sub.get("key", []):
            raise error.CustomException(
                401, "Desculpe, você não tem permissão."
            )
        return sub
    except jwt.ExpiredSignatureError:
        raise error.CustomException(401, "Desculpe, o token expirou.")
    except jwt.InvalidTokenError:
        raise error.CustomException(401, "Desculpe, o token é inválido.")

    except Exception as e:
        raise error.custom_HTTPException(e)


class Key:
    """Classe para verificação de níveis de permissão via OAuth2"""

    async def n5(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """Verifica se o usuário tem o nível de permissão máximo N5"""
        payload = decode_token(token, db, 5)
        return payload

    async def n4(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """Verifica se o usuário tem o nível de permissão N4"""
        payload = decode_token(token, db, 4)
        return payload

    async def n3(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """Verifica se o usuário tem o nível de permissão N3"""
        payload = decode_token(token, db, 3)
        return payload

    async def n2(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """Verifica se o usuário tem o nível de permissão N2"""
        payload = decode_token(token, db, 2)
        return payload

    async def n1(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """Verifica se o usuário tem o nível de permissão mínima N1"""
        payload = decode_token(token, db, 1)
        return payload

    async def n0():
        """Endpoint público sem autenticação"""
        return None
