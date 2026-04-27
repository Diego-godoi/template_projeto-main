from fastapi.testclient import TestClient

from app.auth import get_current_payload
from app.core.config import settings
from app.main import app


def test_user_roles_crud_fluxo_completo(client: TestClient, db_session):
    API_PREFIX = settings.API_URL_PREFIX

    # Precisamos criar um user e uma role base para vincular
    from tests.test_roles_service import _criar_role
    from tests.test_users_service import _criar_usuario

    user1, _ = _criar_usuario(db_session)
    role1 = _criar_role(db_session, name="ROLE_LINK_1")

    async def override_admin():
        return {"user_id": str(user1.id), "scopes": ["admin"]}

    app.dependency_overrides[get_current_payload] = override_admin
    try:
        # 1. Post (Create vínculo)
        payload = {"user_id": str(user1.id), "role_id": str(role1.id)}

        resp_post = client.post(f"{API_PREFIX}/user-roles/", json=payload)
        assert resp_post.status_code == 201
        data = resp_post.json()
        assert data["user_id"] == str(user1.id)
        assert data["role_id"] == str(role1.id)
        ur_id = data["id"]

        # 2. Get (Read list)
        resp_get = client.get(f"{API_PREFIX}/user-roles/")
        assert resp_get.status_code == 200
        get_data = resp_get.json()
        assert "data" in get_data
        assert any(ur["id"] == ur_id for ur in get_data["data"])

        # 3. Patch (Update vínculo mudando a Role)
        role2 = _criar_role(db_session, name="ROLE_LINK_2")
        patch_payload = {"role_id": str(role2.id)}

        resp_patch = client.patch(
            f"{API_PREFIX}/user-roles/{ur_id}", json=patch_payload
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["role_id"] == str(role2.id)

        # 4. Delete (Remove vínculo)
        resp_delete = client.delete(f"{API_PREFIX}/user-roles/{ur_id}")
        assert resp_delete.status_code == 204

        # Consulta não tem mais o vínculo
        resp_get_after = client.get(f"{API_PREFIX}/user-roles/")
        assert not any(
            ur["id"] == ur_id for ur in resp_get_after.json()["data"]
        )

    finally:
        app.dependency_overrides.pop(get_current_payload, None)
