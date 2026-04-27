import logging

import bcrypt

from app import error

__all__ = ["get_password_hash", "verify_password"]


def verify_password(
    plain_password: str | bytes, hashed_password: str | bytes
) -> bool:
    try:
        if not isinstance(plain_password, bytes):
            plain_password = plain_password.encode("utf-8")
        if not isinstance(hashed_password, bytes):
            hashed_password = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        logging.error(
            "Exceção inesperada capturada [%s]: %s", type(e).__name__, str(e)
        )
        raise error.CustomException(
            status_code=500,
            detail="Erro Interno da API",
        )


def get_password_hash(password: str | bytes) -> str:
    try:
        if not isinstance(password, bytes):
            password = password.encode("utf-8")
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        logging.error(
            "Exceção inesperada capturada [%s]: %s", type(e).__name__, str(e)
        )
        raise error.CustomException(
            status_code=500,
            detail="Erro Interno da API",
        )
