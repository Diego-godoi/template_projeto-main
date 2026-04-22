# tests/test_users_api.py
"""
Testes end-to-end do endpoint de usuários (Épico 5.2).

Utiliza o TestClient do FastAPI.
"""

from faker import Faker
from fastapi.testclient import TestClient

from app.auth import Key
from app.core.config import settings
from app.main import app

fake = Faker("pt_BR")

# Prefixo da API
API_PREFIX = settings.API_URL_PREFIX


def test_post_usuario_retorna_201(client: TestClient):
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

    response = client.post(f"{API_PREFIX}/users/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == payload["email"]


def test_post_usuario_email_duplicado_retorna_422(client: TestClient):
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
    client.post(f"{API_PREFIX}/users/", json=payload1)

    # Tentar criar o segundo com o mesmo email e CPF diferente
    cpf2_raw = fake.cpf().replace(".", "").replace("-", "")
    payload2 = {
        "email": email,  # e-mail duplicado
        "password": "SenhaForte@123",
        "full_name": fake.name(),
        "cpf": cpf2_raw,
        "active": True,
    }

    response2 = client.post(f"{API_PREFIX}/users/", json=payload2)
    assert response2.status_code == 422

    data = response2.json()
    # Verifica se a mensagem diz que o erro é no campo body -> email
    assert any(err["loc"][-1] == "email" for err in data["detail"])


def test_get_usuarios_retorna_200(client: TestClient):
    """
    Testa listagem de usuários retorna 200 OK via GET /users/.
    Requer override de autenticação (Key.n1).
    """

    # Mock para by-pass na autenticação n1
    async def override_n1():
        return {"user_id": "test", "key": [1]}

    app.dependency_overrides[Key.n1] = override_n1

    try:
        response = client.get(f"{API_PREFIX}/users/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
    finally:
        app.dependency_overrides.pop(Key.n1, None)


def test_patch_usuario_retorna_200(client: TestClient, db_session):
    from tests.test_users_service import _criar_usuario

    user, _ = _criar_usuario(db_session)

    async def override_n1():
        return {"user_id": str(user.id), "key": [1]}

    app.dependency_overrides[Key.n1] = override_n1

    try:
        novo_nome = "Nome Trocado Via API"
        payload = {"full_name": novo_nome}
        response = client.patch(f"{API_PREFIX}/users/{user.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Nome Trocado Via Api"
    finally:
        app.dependency_overrides.pop(Key.n1, None)


def test_delete_usuario_retorna_204(client: TestClient, db_session):
    from tests.test_users_service import _criar_usuario

    user, _ = _criar_usuario(db_session)

    async def override_n1():
        return {"user_id": str(user.id), "key": [1]}

    app.dependency_overrides[Key.n1] = override_n1

    try:
        response = client.delete(f"{API_PREFIX}/users/{user.id}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.pop(Key.n1, None)
