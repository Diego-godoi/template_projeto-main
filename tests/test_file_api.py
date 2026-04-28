import os

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_payload
from app.core.config import settings
from app.main import app

API_PREFIX = settings.API_URL_PREFIX


# Mock para by-pass na autenticação (user)
async def override_user():
    return {"user_id": "test", "scopes": ["user"]}


@pytest.fixture
def override_upload_dir(tmp_path):
    # Mocka o UPLOAD_DIR para um diretório temporário
    dir_path = str(tmp_path) + "/"
    os.makedirs(dir_path, exist_ok=True)
    original_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = dir_path

    yield dir_path

    # Teardown
    settings.UPLOAD_DIR = original_dir


@pytest.mark.asyncio
async def test_post_file_success(client: TestClient, override_upload_dir):
    app.dependency_overrides[get_current_payload] = override_user
    try:
        # Simular um arquivo em memória
        file_content = b"Conteudo teste da API"
        files = {"file": ("test_api.txt", file_content, "text/plain")}
        data = {"type_data": "text"}

        response = await client.post(
            f"{API_PREFIX}/file/", files=files, data=data
        )
    finally:
        app.dependency_overrides.pop(get_current_payload, None)

    assert response.status_code == 200
    filename = response.json()
    assert isinstance(filename, str)

    # Verifica se o arquivo foi fisicamente criado no UPLOAD_DIR mockado
    filepath = os.path.join(override_upload_dir, filename)
    assert os.path.exists(filepath)
    with open(filepath, "rb") as f:
        assert f.read() == file_content


@pytest.mark.asyncio
async def test_get_file_by_filename_success(
    client: TestClient, override_upload_dir
):
    app.dependency_overrides[get_current_payload] = override_user
    try:
        import uuid

        # Cria arquivo mockado manualmente
        mock_filename = str(uuid.uuid4())
        filepath = os.path.join(override_upload_dir, mock_filename)
        with open(filepath, "wb") as f:
            f.write(b"Conteudo Mockado GET")

        # Faz o get pelo UUID
        response = await client.get(f"{API_PREFIX}/file/{mock_filename}")
    finally:
        app.dependency_overrides.pop(get_current_payload, None)

    assert response.status_code == 200
    assert response.content == b"Conteudo Mockado GET"


@pytest.mark.asyncio
async def test_get_file_by_filename_not_found(
    client: TestClient, override_upload_dir
):
    app.dependency_overrides[get_current_payload] = override_user
    try:
        import uuid

        fail_filename = str(uuid.uuid4())  # ID válido mas arquivo Inexistente

        response = await client.get(f"{API_PREFIX}/file/{fail_filename}")
    finally:
        app.dependency_overrides.pop(get_current_payload, None)

    assert response.status_code == 404
    assert "Imagem nao encontrada" in response.json()["detail"]
