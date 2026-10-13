from sqlalchemy.ext.asyncio import AsyncSession

from app import schema
from app.core.config import settings

from .factories import RolesFactory, UsersFactory


async def test_user_roles_crud_fluxo_completo(
    client, async_db_session: AsyncSession, auth_as
):
    API_PREFIX = settings.API_URL_PREFIX

    user1 = UsersFactory.create()
    role1 = RolesFactory.create(name="ROLE_LINK_1")

    await async_db_session.flush()

    auth_as(user1, role="Admin")

    payload = schema.PostUserRoles(
        user_id=user1.id, role_id=role1.id
    ).model_dump(mode="json")

    resp_post = await client.post(f"{API_PREFIX}/user-roles/", json=payload)
    assert resp_post.status_code == 201
    data = resp_post.json()
    assert data["user_id"] == str(user1.id)
    assert data["role_id"] == str(role1.id)
    ur_id = data["id"]

    # 2. Get (Read list)
    resp_get = await client.get(f"{API_PREFIX}/user-roles/")
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert "data" in get_data
    assert any(ur["id"] == ur_id for ur in get_data["data"])

    # 3. Patch (Update vínculo mudando a Role)
    role2 = RolesFactory.create(name="ROLE_LINK_2")
    await async_db_session.flush()
    patch_payload = schema.PatchUserRoles(
        role_id=role2.id, user_id=user1.id
    ).model_dump(mode="json")

    resp_patch = await client.patch(
        f"{API_PREFIX}/user-roles/{ur_id}", json=patch_payload
    )
    assert resp_patch.status_code == 200
    assert resp_patch.json()["role_id"] == str(role2.id)

    # 4. Delete (Remove vínculo)
    resp_delete = await client.delete(f"{API_PREFIX}/user-roles/{ur_id}")
    assert resp_delete.status_code == 204

    # Consulta não tem mais o vínculo
    resp_get_after = await client.get(f"{API_PREFIX}/user-roles/")
    assert not any(ur["id"] == ur_id for ur in resp_get_after.json()["data"])
