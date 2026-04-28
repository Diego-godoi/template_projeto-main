from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import core, models, schema

__all__ = ["pop_db"]


roles = [
    {
        "name": "Admin",
        "description": """Responsabilidades: O Admin tem controle total sobre o sistema ou plataforma, o que significa que pode adicionar, modificar ou excluir qualquer conteúdo ou usuário. """,
    },
    {
        "name": "Technician",
        "description": "Técnico, realiza as operações básicas.",
    },
    {
        "name": "Manager",
        "description": "Gerente, tem acesso maior ao dados do painel.",
    },
]

users = [
    {
        "email": core.settings.FIRST_SUPERUSER,
        "full_name": "Admin",
        "cpf": "39604805045",
        "password": core.settings.FIRST_SUPERUSER_PASSWORD,
        "active": True,
        "role": roles[0]["name"],
    }
]


async def pop_db(db: AsyncSession) -> None:
    """Caso exista dados iniciais no banco da aplicação, escrever sua inserçao"""

    for data in roles:
        stmt = select(models.Roles).where(models.Roles.name == data["name"])
        if not (await db.execute(stmt)).scalars().first():
            role_data = models.Roles(**schema.PostRoles(**data).model_dump())
            db.add(role_data)
            await db.commit()

    for data in users:
        stmt = select(models.Users).where(models.Users.email == data["email"])
        if not (await db.execute(stmt)).scalars().first():
            user_data = models.Users(**schema.PostUsers(**data).model_dump())

            # Busca a role explicitamente
            stmt_role = select(models.Roles).where(
                models.Roles.name == data["role"]
            )
            role_obj = (await db.execute(stmt_role)).scalars().first()

            if role_obj:
                user_data.user_roles.append(
                    models.UserRoles(role_id=role_obj.id)
                )

            # Gera o hash da senha antes de salvar
            user_data.password = await core.get_password_hash(data["password"])

            db.add(user_data)
            await db.commit()
