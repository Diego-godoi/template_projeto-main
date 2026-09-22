"""
Ponto central de Factories (FactoryBoy) para os testes do template.

Regras:
- Testes unitários: usar `Factory.build()` -> objeto em memória, sem DB.
- Testes de integração: usar `Factory.create()` -> persistido no banco.
- Schemas Pydantic são construídos diretamente nos testes; factories ficam
  reservadas para entidades ORM que precisam de persistência e relações.
"""

import re
import uuid

import factory
from faker import Faker

from app import models
from app.util.functions import generate_cpf

fake = Faker("pt_BR")

DEFAULT_PASSWORD = "SenhaForte@123"
DEFAULT_PASSWORD_HASH = (
    b"$2b$12$fixedhashedvaluefortestingonly00000000000000000000"
)


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def fake_cpf() -> str:
    return generate_cpf()


class BaseSQLAlchemyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    id = factory.LazyFunction(uuid.uuid4)


class UserFieldsMixin(factory.Factory):
    class Meta:
        abstract = True

    name = factory.Faker("name", locale="pt_BR")
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    cpf = factory.LazyFunction(fake_cpf)


class UsersFactory(UserFieldsMixin, BaseSQLAlchemyFactory):
    class Meta:
        model = models.Users

    password = factory.LazyFunction(lambda: DEFAULT_PASSWORD_HASH)
    is_deleted = False


class RolesFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.Roles

    name = factory.Sequence(lambda n: f"Role_{n}")
    description = factory.Faker("sentence", locale="pt_BR")
    is_system = False


class UserRolesFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.UserRoles

    user = factory.SubFactory(UsersFactory)
    role = factory.SubFactory(RolesFactory)
    user_id = factory.LazyAttribute(lambda o: o.user.id)
    role_id = factory.LazyAttribute(lambda o: o.role.id)


# Lista para injeção via conftest
SQLALCHEMY_FACTORIES = [
    UsersFactory,
    RolesFactory,
    UserRolesFactory,
]
