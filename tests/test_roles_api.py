import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import util
from app.core.config import settings

from .factories import PatchRolesFactory, PostRolesFactory, UsersFactory

API_PREFIX = settings.API_URL_PREFIX


@pytest.mark.asyncio
async def test_roles_crud_fluxo_completo(
    client, async_db_session: AsyncSession, auth_as
):
    user = UsersFactory.create()
    await async_db_session.flush()

    auth_as(
        user, ["read:roles", "write:roles", "update:roles", "delete:roles"]
    )
    # 1. Post (Create)

    payload = PostRolesFactory.build().model_dump(mode="json")

    resp_post = await client.post(f"{API_PREFIX}/roles/", json=payload)
    assert resp_post.status_code == 201
    data = resp_post.json()
    assert data["name"].lower() == payload["name"].lower()
    role_id = data["id"]

    # 2. Get (Read list)
    resp_get = await client.get(f"{API_PREFIX}/roles/")
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert "data" in get_data
    assert any(r["id"] == role_id for r in get_data["data"])

    # 3. Patch (Update)
    patch_payload = PatchRolesFactory.build().model_dump(mode="json")
    resp_patch = await client.patch(
        f"{API_PREFIX}/roles/{role_id}", json=patch_payload
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["name"] == util.normalize_capitalize(
        patch_payload["name"]
    )

    # 4. Delete (Remove)
    resp_delete = await client.delete(f"{API_PREFIX}/roles/{role_id}")
    assert resp_delete.status_code == 204

    # Confirma remoção
    resp_get_after = await client.get(f"{API_PREFIX}/roles/")
    assert not any(r["id"] == role_id for r in resp_get_after.json()["data"])
