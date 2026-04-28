import asyncio
import logging

import bcrypt

from app import error

__all__ = ["get_password_hash", "verify_password"]


async def verify_password(
    plain_password: str | bytes, hashed_password: str | bytes
) -> bool:
    try:
        if not isinstance(plain_password, bytes):
            plain_password = await asyncio.to_thread(
                lambda: plain_password.encode("utf-8")
            )
        if not isinstance(hashed_password, bytes):
            hashed_password = await asyncio.to_thread(
                lambda: hashed_password.encode("utf-8")
            )
        return await asyncio.to_thread(
            lambda: bcrypt.checkpw(plain_password, hashed_password)
        )
    except Exception as e:
        logging.error(
            "Exceção inesperada capturada [%s]: %s", type(e).__name__, str(e)
        )
        raise error.CustomException(
            status_code=500,
            detail="Erro Interno da API",
        )


async def get_password_hash(password: str | bytes) -> bytes:
    try:
        if isinstance(password, str):
            password = password.encode("utf-8")
        return await asyncio.to_thread(
            lambda: bcrypt.hashpw(password, bcrypt.gensalt())
        )
    except Exception as e:
        logging.error(
            "Exceção inesperada capturada [%s]: %s", type(e).__name__, str(e)
        )
        raise error.CustomException(
            status_code=500,
            detail="Erro Interno da API",
        )
