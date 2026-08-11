from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import error
from app.models import Permissions
from app.services.permissions_service import PermissionsService
from app.util.annotated import QueryParameters

from .factories import (
    PatchPermissionsFactory,
    PermissionsFactory,
    PostPermissionsFactory,
)


@pytest.mark.asyncio
async def test_create_permission_com_sucesso(async_db_session: AsyncSession):
    permission_payload = PostPermissionsFactory.build(name="create:module")
    result = await PermissionsService.create_permission(
        permission_payload, async_db_session
    )
    assert result.id is not None
    assert result.name == "create:module"


@pytest.mark.asyncio
async def test_create_permission_nome_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    PermissionsFactory.create(name="create:module")
    await async_db_session.flush()

    schema_duplicado = PostPermissionsFactory.build(name="create:module")
    with pytest.raises(error.ValidationException) as exc_info:
        await PermissionsService.create_permission(
            schema_duplicado, async_db_session
        )

    errors = exc_info.value.detail
    # Verifica que o erro levantado avisa que nome já está cadastrado
    assert any("já está cadastrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_permission_com_sucesso(async_db_session: AsyncSession):
    permission = PermissionsFactory.create(name="create:module")
    await async_db_session.flush()

    schema_patch = PatchPermissionsFactory.build(name=None, module="module")
    permission_atualizada = await PermissionsService.patch_permission(
        permission.id, schema_patch, async_db_session
    )

    assert permission_atualizada.module == "module"
    assert permission_atualizada.name == "create:module"  # Não alterado


@pytest.mark.asyncio
async def test_patch_permission_nome_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    PermissionsFactory.create(name="create:module")
    permission2 = PermissionsFactory.create(name="update:module")
    await async_db_session.flush()

    schema_patch = PatchPermissionsFactory.build(name="create:module")
    with pytest.raises(error.ValidationException) as exc_info:
        await PermissionsService.patch_permission(
            permission2.id, schema_patch, async_db_session
        )

    errors = exc_info.value.detail
    assert any("já está cadastrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_permission_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    schema_patch = PatchPermissionsFactory.build(name="create:module")
    with pytest.raises(error.CustomException) as exc_info:
        await PermissionsService.patch_permission(
            uuid4(), schema_patch, async_db_session
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_permission_com_sucesso(async_db_session: AsyncSession):
    permission = PermissionsFactory.create(name="delete:module")
    await async_db_session.flush()
    permission_id = permission.id

    await PermissionsService.delete_permission(permission_id, async_db_session)
    assert await async_db_session.get(Permissions, permission_id) is None


@pytest.mark.asyncio
async def test_delete_permission_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    with pytest.raises(error.CustomException) as exc_info:
        await PermissionsService.delete_permission(uuid4(), async_db_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_permissions_paginado(async_db_session: AsyncSession):
    PermissionsFactory.create(name="create:module")
    PermissionsFactory.create(name="update:module")
    await async_db_session.flush()

    qp = QueryParameters(
        all_data=True,
        limit=10,
        skip=0,
        operator="=",
        attribute=None,
        value=None,
        json_string=None,
        include=None,
    )
    result = await PermissionsService.get_permissions(qp, async_db_session)

    assert result is not None
    if isinstance(result, dict):
        assert "data" in result or "items" in result
    else:
        assert hasattr(result, "data") or hasattr(result, "items")
