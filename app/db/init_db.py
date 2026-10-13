import logging
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import core, models

__all__ = ["pop_db"]

logger = logging.getLogger(__name__)

users = [
    {
        "name": "Admin",
        "email": core.settings.FIRST_SUPERUSER,
        "cpf": "39604805045",
        "password": core.settings.FIRST_SUPERUSER_PASSWORD,
        "role": "Admin",
    }
]


async def _get_by_field(db: AsyncSession, model, field_name: str, value):
    stmt = select(model).where(getattr(model, field_name) == value)
    return (await db.execute(stmt)).scalars().first()


async def _ensure_default_users(
    db: AsyncSession, data: Iterable[dict]
) -> None:
    for item in data:
        if await _get_by_field(db, models.Users, "email", item["email"]):
            continue

        role = await _get_by_field(db, models.Roles, "name", item["role"])
        if role is None:
            raise RuntimeError(
                f"Role '{item['role']}' não encontrada. "
                "Rode as migrations (seed de roles) antes do pop_db."
            )

        user = models.Users(
            name=item["name"],
            email=item["email"],
            cpf=item["cpf"],
            password=await core.get_password_hash(item["password"]),
        )
        user.user_roles.append(models.UserRoles(role=role))
        db.add(user)
        logger.info("Usuário padrão '%s' criado", item["email"])

    await db.commit()


async def pop_db(db: AsyncSession) -> None:
    """Popula o administrador padrão de forma idempotente."""
    await _ensure_default_users(db, users)
