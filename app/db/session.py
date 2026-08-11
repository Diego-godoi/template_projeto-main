from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import core

__all__ = ["AsyncSessionLocal", "_db", "engine", "get_db"]

engine = create_async_engine(
    core.settings.get_async_db_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


async def get_db():
    try:
        db = AsyncSessionLocal()
        yield db
    finally:
        await db.close()


_db = Annotated[AsyncSession, Depends(get_db)]
