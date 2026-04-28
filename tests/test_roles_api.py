import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_payload
from app.core.config import settings
from app.main import app

fake = Faker("pt_BR")
API_PREFIX = settings.API_URL_PREFIX


# Mock para by-pass na autenticação (admin)
async def override_admin():
    return {"user_id": "test", "scopes": ["admin"]}


@pytest.mark.asyncio
async def test_roles_crud_fluxo_completo(
    client, async_db_session: AsyncSession
):
    app.dependency_overrides[get_current_payload] = override_admin
    try:
        # 1. Post (Create)
        role_name = "Gerente de Projeto " + fake.word()
        payload = {"name": role_name, "description": "Desc"}

        resp_post = await client.post(f"{API_PREFIX}/roles/", json=payload)
        assert resp_post.status_code == 201
        data = resp_post.json()
        assert data["name"].lower() == role_name.lower()
        role_id = data["id"]

        # 2. Get (Read list)
        resp_get = await client.get(f"{API_PREFIX}/roles/")
        assert resp_get.status_code == 200
        get_data = resp_get.json()
        assert "data" in get_data
        assert any(r["id"] == role_id for r in get_data["data"])

        # 3. Patch (Update)
        novo_nome = "DIRETOR GERAL " + fake.word()
        patch_payload = {"name": novo_nome}
        resp_patch = await client.patch(
            f"{API_PREFIX}/roles/{role_id}", json=patch_payload
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["name"] == novo_nome

        # 4. Delete (Remove)
        resp_delete = await client.delete(f"{API_PREFIX}/roles/{role_id}")
        assert resp_delete.status_code == 204

        # Confirma remoção
        resp_get_after = await client.get(f"{API_PREFIX}/roles/")
        assert not any(
            r["id"] == role_id for r in resp_get_after.json()["data"]
        )

    finally:
        app.dependency_overrides.pop(get_current_payload, None)
