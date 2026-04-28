import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_payload
from app.core.config import settings
from app.main import app

fake = Faker("pt_BR")

# Prefixo da API
API_PREFIX = settings.API_URL_PREFIX


@pytest.mark.asyncio
async def test_post_usuario_retorna_201(client):
    """
    Testa se o endpoint de criação de usuário retorna 201 Created.
    """
    cpf_raw = fake.cpf().replace(".", "").replace("-", "")

    payload = {
        "email": fake.unique.email(),
        "password": "SenhaForte@123",
        "full_name": fake.name(),
        "cpf": cpf_raw,
        "active": True,
    }

    response = await client.post(f"{API_PREFIX}/users/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == payload["email"]


@pytest.mark.asyncio
async def test_post_usuario_email_duplicado_retorna_422(client):
    """
    Criar usuário com email duplicado retorna 422 Unprocessable Entity.
    """
    cpf_raw = fake.cpf().replace(".", "").replace("-", "")
    email = fake.unique.email()

    payload1 = {
        "email": email,
        "password": "SenhaForte@123",
        "full_name": fake.name(),
        "cpf": cpf_raw,
        "active": True,
    }
    # Criar o primeiro
    await client.post(f"{API_PREFIX}/users/", json=payload1)

    # Tentar criar o segundo com o mesmo email e CPF diferente
    cpf2_raw = fake.cpf().replace(".", "").replace("-", "")
    payload2 = {
        "email": email,  # e-mail duplicado
        "password": "SenhaForte@123",
        "full_name": fake.name(),
        "cpf": cpf2_raw,
        "active": True,
    }

    response2 = await client.post(f"{API_PREFIX}/users/", json=payload2)
    assert response2.status_code == 422

    data = response2.json()
    # Verifica se a mensagem diz que o erro é no campo body -> email
    assert any(err["loc"][-1] == "email" for err in data["detail"])


@pytest.mark.asyncio
async def test_get_usuarios_retorna_200(client):
    """
    Testa listagem de usuários retorna 200 OK via GET /users/.
    Requer override de autenticação (scope: user).
    """

    # Mock para by-pass na autenticação (user)
    async def override_user():
        return {"user_id": "test", "scopes": ["user"]}

    app.dependency_overrides[get_current_payload] = override_user

    try:
        response = await client.get(f"{API_PREFIX}/users/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
    finally:
        app.dependency_overrides.pop(get_current_payload, None)


@pytest.mark.asyncio
async def test_patch_usuario_retorna_200(
    client, async_db_session: AsyncSession
):
    from tests.test_users_service import _criar_usuario

    user, _ = await _criar_usuario(async_db_session)

    async def override_user():
        return {"user_id": str(user.id), "scopes": ["user"]}

    app.dependency_overrides[get_current_payload] = override_user

    try:
        novo_nome = "Nome Trocado Via API"
        payload = {"full_name": novo_nome}
        response = await client.patch(
            f"{API_PREFIX}/users/{user.id}", json=payload
        )
        assert response.status_code == 200
        # A normalização pode mudar o case dependendo da implementação, mas o service usa lower em alguns campos e title em outros.
        # No users_service.py: user_data.full_name = normalize_title(schema.full_name)
        assert response.json()["full_name"] == "Nome Trocado Via Api"
    finally:
        app.dependency_overrides.pop(get_current_payload, None)


@pytest.mark.asyncio
async def test_delete_usuario_retorna_204(
    client, async_db_session: AsyncSession
):
    from tests.test_users_service import _criar_usuario

    user, _ = await _criar_usuario(async_db_session)

    async def override_user():
        return {"user_id": str(user.id), "scopes": ["user"]}

    app.dependency_overrides[get_current_payload] = override_user

    try:
        response = await client.delete(f"{API_PREFIX}/users/{user.id}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.pop(get_current_payload, None)
