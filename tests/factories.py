"""
Ponto central de Factories (FactoryBoy) para os testes do template.

Regras:
- Testes unitários: usar `Factory.build()` -> objeto em memória, sem DB.
- Testes de integração: usar `Factory.create()` -> persistido no banco.
- Payloads de request (schemas Pydantic): usar `PostUsersFactory()` /
  `PatchUsersFactory()` -> geram instâncias já validadas pelo Pydantic,
  com dados únicos via Faker, sem tocar no banco.
"""

import uuid

import factory
from faker import Faker

from app import models, schema

fake = Faker("pt_BR")

DEFAULT_PASSWORD = "SenhaForte@123"
DEFAULT_PASSWORD_HASH = (
    b"$2b$12$fixedhashedvaluefortestingonly00000000000000000000"
)

# -----------------------------------------------------------------------------
# SQLAlchemy Models
# -----------------------------------------------------------------------------


class UsersFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Users
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("name", locale="pt_BR")
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    cpf = factory.LazyAttribute(
        lambda o: fake.unique.cpf().replace(".", "").replace("-", "")
    )
    password = factory.LazyFunction(lambda: DEFAULT_PASSWORD_HASH)
    active = True


class RolesFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Roles
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Role_{n}")
    description = factory.Faker("sentence", locale="pt_BR")
    is_system = False


class UserRolesFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.UserRoles
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UsersFactory)
    role = factory.SubFactory(RolesFactory)
    user_id = factory.LazyAttribute(lambda o: o.user.id)
    role_id = factory.LazyAttribute(lambda o: o.role.id)


class PermissionsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Permissions
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"read:module_{n}")
    module = factory.Sequence(lambda n: f"module_{n}")


class RolePermissionsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.RolePermissions
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    id = factory.LazyFunction(uuid.uuid4)
    role_id = factory.LazyAttribute(lambda o: o.role.id)
    permission_id = factory.LazyAttribute(lambda o: o.permission.id)

    role = factory.SubFactory(RolesFactory)
    permission = factory.SubFactory(PermissionsFactory)


# Lista para injeção via conftest
SQLALCHEMY_FACTORIES = [
    UsersFactory,
    RolesFactory,
    UserRolesFactory,
    PermissionsFactory,
    RolePermissionsFactory,
]

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------


class PostUsersFactory(factory.Factory):
    class Meta:
        model = schema.PostUsers

    name = factory.Faker("name", locale="pt_BR")
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    cpf = factory.LazyAttribute(
        lambda o: fake.unique.cpf().replace(".", "").replace("-", "")
    )
    active = True
    password = DEFAULT_PASSWORD


class PatchUsersFactory(factory.Factory):
    class Meta:
        model = schema.PatchUsers

    name = factory.Faker("name", locale="pt_BR")


class PostUserRolesFactory(factory.Factory):
    class Meta:
        model = schema.PostUserRoles

    user_id = factory.LazyFunction(uuid.uuid4)
    role_id = factory.LazyFunction(uuid.uuid4)


class PatchUserRolesFactory(factory.Factory):
    class Meta:
        model = schema.PatchUserRoles

    user_id = factory.LazyFunction(uuid.uuid4)
    role_id = factory.LazyFunction(uuid.uuid4)


class PostRolesFactory(factory.Factory):
    class Meta:
        model = schema.PostRoles

    name = factory.Faker("word", locale="pt_BR")
    description = factory.Faker("sentence", locale="pt_BR")


class PatchRolesFactory(factory.Factory):
    class Meta:
        model = schema.PatchRoles

    name = factory.Faker("word", locale="pt_BR")
    description = factory.Faker("sentence", locale="pt_BR")


class PostPermissionsFactory(factory.Factory):
    class Meta:
        model = schema.PostPermissions

    name = factory.Sequence(lambda n: f"write:module_{n}")
    module = factory.Sequence(lambda n: f"module_{n}")


class PatchPermissionsFactory(factory.Factory):
    class Meta:
        model = schema.PatchPermissions

    name = factory.Sequence(lambda n: f"write:module_{n}")
    module = factory.Sequence(lambda n: f"module_{n}")


class PostRolePermissionsFactory(factory.Factory):
    class Meta:
        model = schema.PostRolePermissions

    role_id = factory.LazyFunction(uuid.uuid4)
    permission_id = factory.LazyFunction(uuid.uuid4)


class PatchRolePermissionsFactory(factory.Factory):
    class Meta:
        model = schema.PatchRolePermissions

    role_id = factory.LazyFunction(uuid.uuid4)
    permission_id = factory.LazyFunction(uuid.uuid4)
