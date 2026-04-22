from sqlalchemy.orm import Session

from app import core, models, schema

__all__ = ["pop_db"]


roles = [
    {
        "name": "Admin",
        "access_level": 10,
        "description": """Responsabilidades: O Admin tem controle total sobre o sistema ou plataforma, o que significa que pode adicionar, modificar ou excluir qualquer conteúdo ou usuário. """,
    },
    {
        "name": "technician",
        "access_level": 1,
        "description": "Técnico, realiza as operações básicas.",
    },
    {
        "name": "manager",
        "access_level": 2,
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


def pop_db(db: Session) -> None:
    """Caso exista dados iniciais no banco da aplicação, escrever sua inserçao"""

    for data in roles:
        if not models.Roles.get(db, "name", data["name"]):
            role_data = models.Roles(**schema.PostRoles(**data).model_dump())
            role_data.create(db)

    for data in users:
        if not models.Users.get(db, "email", data["email"]):
            user_data = models.Users(**schema.PostUsers(**data).model_dump())
            role_data = models.Roles.get(db, "name", data["role"])
            user_data.user_roles.append(
                models.UserRoles(role_id=str(role_data.id))
            )
            user_data.create(db)
