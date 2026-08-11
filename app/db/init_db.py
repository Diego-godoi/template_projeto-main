from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import core, models, schema

__all__ = ["SYSTEM_SCOPES", "pop_db"]

# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
PERMISSION_DEFINITIONS: dict[str, list[str]] = {
    "users": ["read", "update", "delete", "approve"],
    "roles": ["read", "write", "update", "delete"],
    "permissions": ["read", "write", "update", "delete"],
    "user-roles": ["read", "write", "update", "delete"],
    "role-permissions": ["read", "write", "update", "delete"],
    "files": ["read"],
}

_EXTRA_PERMISSIONS = [
    {"name": "read:me", "module": "me"},
    {"name": "update:me", "module": "me"},
]


def _build_permissions() -> list[dict]:
    generated = [
        {"name": f"{action}:{module}", "module": module}
        for module, actions in PERMISSION_DEFINITIONS.items()
        for action in actions
    ]
    return _EXTRA_PERMISSIONS + generated


permissions: list[dict] = _build_permissions()
_all_permission_names: list[str] = [p["name"] for p in permissions]

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
roles = [
    {
        "name": "User",
        "description": "Usuário comum do sistema.",
        "is_system": True,
    },
    {
        "name": "Manager",
        "description": "Gestor com acesso de leitura aos usuários e roles.",
        "is_system": True,
    },
    {
        "name": "Admin",
        "description": "Administrador. Controle total sobre o sistema.",
        "is_system": True,
    },
]

# ---------------------------------------------------------------------------
# Mapeamento role -> permissions
# ---------------------------------------------------------------------------
_USER_PERMISSIONS = [
    "read:me",
    "update:me",
    "read:files",
]

_MANAGER_PERMISSIONS = _USER_PERMISSIONS + [
    "read:users",
    "approve:users",
    "read:roles",
]

role_permissions_map: dict[str, list[str]] = {
    "User": _USER_PERMISSIONS,
    "Manager": _MANAGER_PERMISSIONS,
    "Admin": _all_permission_names,
}

# ---------------------------------------------------------------------------
# Admin padrão
# ---------------------------------------------------------------------------
users = [
    {
        "email": core.settings.FIRST_SUPERUSER,
        "name": "Admin",
        "cpf": "39604805045",
        "password": core.settings.FIRST_SUPERUSER_PASSWORD,
        "active": True,
        "role": "Admin",
    }
]


# ---------------------------------------------------------------------------
# Helpers genéricos de upsert
# ---------------------------------------------------------------------------
async def _get_by_field(db: AsyncSession, model, field_name: str, value):
    stmt = select(model).where(getattr(model, field_name) == value)
    return (await db.execute(stmt)).scalars().first()


async def _ensure_permissions(db: AsyncSession, data: Iterable[dict]) -> None:
    for item in data:
        if await _get_by_field(db, models.Permissions, "name", item["name"]):
            continue
        db.add(
            models.Permissions(**schema.PostPermissions(**item).model_dump())
        )
    await db.commit()


async def _ensure_roles(db: AsyncSession, data: Iterable[dict]) -> None:
    for item in data:
        if await _get_by_field(db, models.Roles, "name", item["name"]):
            continue
        db.add(models.Roles(**schema.PostRoles(**item).model_dump()))
    await db.commit()


async def _ensure_role_permissions(
    db: AsyncSession, mapping: dict[str, list[str]]
) -> None:
    for role_name, permission_names in mapping.items():
        role_obj = await _get_by_field(db, models.Roles, "name", role_name)
        if not role_obj:
            continue

        for permission_name in permission_names:
            permission_obj = await _get_by_field(
                db, models.Permissions, "name", permission_name
            )
            if not permission_obj:
                continue

            stmt = select(models.RolePermissions).where(
                models.RolePermissions.role_id == role_obj.id,
                models.RolePermissions.permission_id == permission_obj.id,
            )
            if (await db.execute(stmt)).scalars().first():
                continue

            db.add(
                models.RolePermissions(
                    role_id=role_obj.id, permission_id=permission_obj.id
                )
            )
        await db.commit()


async def _ensure_default_users(
    db: AsyncSession, data: Iterable[dict]
) -> None:
    for item in data:
        if await _get_by_field(db, models.Users, "email", item["email"]):
            continue

        user_data = models.Users(**schema.PostUsers(**item).model_dump())
        role_obj = await _get_by_field(db, models.Roles, "name", item["role"])
        if role_obj:
            user_data.user_roles.append(models.UserRoles(role_id=role_obj.id))

        user_data.password = await core.get_password_hash(item["password"])
        db.add(user_data)
        await db.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def pop_db(db: AsyncSession) -> None:
    """Popula dados iniciais indispensáveis para o sistema (idempotente)."""
    await _ensure_permissions(db, permissions)
    await _ensure_roles(db, roles)
    await _ensure_role_permissions(db, role_permissions_map)
    await _ensure_default_users(db, users)


def build_scopes_map() -> dict[str, str]:
    """Gera um dicionário de scopes no formato exigido pelo FastAPI/Swagger."""
    scopes_map = {}
    for module, actions in PERMISSION_DEFINITIONS.items():
        for action in actions:
            scopes_map[f"{action}:{module}"] = (
                f"Permissão para {action.upper()} no módulo {module}"
            )
    for extra in _EXTRA_PERMISSIONS:
        scopes_map[extra["name"]] = (
            f"Permissão especial para {extra['name'].upper()}"
        )
    return scopes_map


SYSTEM_SCOPES = build_scopes_map()
