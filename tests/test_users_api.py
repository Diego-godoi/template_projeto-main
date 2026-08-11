# tests/test_users_api.py

import pytest

from app import models
from app.core.config import settings
from app.util import functions
from tests.factories import (
    PatchUsersFactory,
    PostUsersFactory,
    RolesFactory,
    UsersFactory,
)

API_PREFIX = settings.API_URL_PREFIX

# ===========================================================================
# TESTES DE ENDPOINT
# ===========================================================================


@pytest.mark.asyncio
async def test_post_usuario_retorna_201(client):
    """Testa se o endpoint de criação de usuário retorna 201 Created."""
    RolesFactory.create(name=models.enums.StandardRoles.USER.value)

    cpf_valido = functions.generate_cpf()
    payload = PostUsersFactory.build(cpf=cpf_valido)

    response = await client.post(
        f"{API_PREFIX}/users/",
        data=payload.model_dump(mode="json"),
    )

    assert response.status_code == 201, f"Response body: {response.json()}"


@pytest.mark.asyncio
async def test_patch_usuario_retorna_200(client, auth_as):
    """Testa atualização parcial do usuário via PATCH."""
    user = UsersFactory.create()
    auth_as(user, ["update:users"])

    payload = PatchUsersFactory.build()
    data = payload.model_dump(
        mode="json", exclude_unset=True, exclude_none=True
    )

    response = await client.patch(f"{API_PREFIX}/users/{user.id}", data=data)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_usuario_retorna_204(client, auth_as):
    """Testa remoção (soft delete) do usuário via DELETE."""
    user = UsersFactory.create()
    auth_as(user, ["delete:users"])

    response = await client.delete(f"{API_PREFIX}/users/{user.id}")
    assert response.status_code == 204
