"""
Ponto central de Factories (FactoryBoy) para os testes do template.

Regras:
- Testes unitários: usar `Factory.build()` -> objeto em memória, sem DB.
- Testes de integração: usar ` Factory.create_async()` -> persistido no banco.
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


def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _fake_cpf() -> str:
    return generate_cpf()


def _fake_phone() -> str:
    ddd = fake.random_int(min=11, max=99)
    subscriber = fake.random_number(digits=8, fix_len=True)
    return f"{ddd}9{subscriber:08d}"


class BaseSQLAlchemyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    @classmethod
    async def create_async(cls, **kwargs):
        """Cria e salva um objeto no banco de forma assíncrona."""
        # 1. Constrói o objeto (e seus relacionamentos) apenas em memória
        obj = cls.build(**kwargs)

        # 2. Salva no banco de dados
        session = cls._meta.sqlalchemy_session
        session.add(obj)
        await session.commit()
        await session.refresh(obj)

        return obj

    @classmethod
    async def create_batch_async(cls, size: int, **kwargs):
        """Cria e salva múltiplos objetos de forma assíncrona."""
        objs = cls.build_batch(size, **kwargs)

        session = cls._meta.sqlalchemy_session
        session.add_all(objs)
        await session.commit()

        for obj in objs:
            await session.refresh(obj)

        return objs

    id = factory.LazyFunction(uuid.uuid4)


class UsersFactory(BaseSQLAlchemyFactory):
    class Meta:
        model = models.Users

    name = factory.Faker("name", locale="pt_BR")
    email = factory.LazyAttribute(lambda o: fake.unique.email())
    cpf = factory.LazyFunction(_fake_cpf)
    password = factory.LazyFunction(lambda: DEFAULT_PASSWORD_HASH)
    is_deleted = factory.lazy_attribute(lambda o: False)


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
