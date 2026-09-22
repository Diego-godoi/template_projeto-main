# tests/test_users_api.py

import pytest

from app import models, schema
from app.core.config import settings
from app.util import functions
from tests.factories import RolesFactory, UsersFactory

API_PREFIX = settings.API_URL_PREFIX

# ===========================================================================
# TESTES DE ENDPOINT
# ===========================================================================


@pytest.mark.asyncio
async def test_post_usuario_retorna_201(client):
    """Testa se o endpoint de criação de usuário retorna 201 Created."""
    RolesFactory.create(name=models.enums.StandardRoles.USER.value)

    cpf_valido = functions.generate_cpf()
    payload = schema.PostUsers(
        name="Usuário de teste",
        email="novo.usuario@example.com",
        cpf=cpf_valido,
        password="SenhaForte@123",
    )

    response = await client.post(
        f"{API_PREFIX}/users/",
        data=payload.model_dump(mode="json"),
    )

    assert response.status_code == 201, f"Response body: {response.json()}"


@pytest.mark.asyncio
async def test_patch_usuario_retorna_200(client, auth_as):
    """Testa atualização parcial do usuário via PATCH."""
    user = UsersFactory.create()
    auth_as(user, role="Admin")

    payload = schema.PatchUsers(name="Nome atualizado")
    data = payload.model_dump(mode="json")

    response = await client.patch(f"{API_PREFIX}/users/{user.id}", data=data)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_usuario_retorna_204(client, auth_as):
    """Testa remoção (soft delete) do usuário via DELETE."""
    user = UsersFactory.create()
    auth_as(user, role="Admin")

    response = await client.delete(f"{API_PREFIX}/users/{user.id}")
    assert response.status_code == 204
