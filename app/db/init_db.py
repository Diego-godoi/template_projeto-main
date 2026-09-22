from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import core, models, schema

__all__ = ["pop_db"]

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
        user_data = models.Users(
            **schema.PostUsers(
                **{k: v for k, v in item.items() if k != "role"}
            ).model_dump()
        )
        user_data.password = await core.get_password_hash(item["password"])
        if role:
            user_data.user_roles.append(models.UserRoles(role=role))
        db.add(user_data)
    await db.commit()


async def pop_db(db: AsyncSession) -> None:
    """Popula o administrador padrão de forma idempotente."""
    await _ensure_default_users(db, users)
