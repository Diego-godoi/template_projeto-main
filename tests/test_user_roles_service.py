from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import error, schema
from app.models import UserRoles
from app.services.user_roles_service import UserRolesService
from app.util.annotated import QueryParameters

from .factories import RolesFactory, UserRolesFactory


@pytest.mark.asyncio
async def test_create_user_role_com_sucesso(async_db_session: AsyncSession):
    user_role = UserRolesFactory.create()
    await async_db_session.flush()

    assert user_role.id is not None
    assert user_role.user_id is not None
    assert user_role.role_id is not None


@pytest.mark.asyncio
async def test_create_user_role_referencias_invalidas_levanta_erro(
    async_db_session: AsyncSession,
):
    payload = schema.PostUserRoles(user_id=uuid4(), role_id=uuid4())

    with pytest.raises(error.ValidationException) as exc_info:
        await UserRolesService.create_user_role(payload, async_db_session)

    errors = exc_info.value.detail
    # Deve estourar duas falhas: user_id e role_id não encontrados
    assert len(errors) == 2
    assert any("usuario não encontrado" in err["msg"] for err in errors)
    assert any("papel não encontrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_user_role_com_sucesso(async_db_session: AsyncSession):
    user_role = UserRolesFactory.create()
    new_role = RolesFactory.create()

    await async_db_session.flush()

    schema_patch = schema.PatchUserRoles(
        role_id=new_role.id, user_id=user_role.user_id
    )

    user_role_atualizada = await UserRolesService.patch_user_role(
        user_role.id, schema_patch, async_db_session
    )

    assert user_role_atualizada.role_id == new_role.id


@pytest.mark.asyncio
async def test_patch_user_role_referencias_invalidas_levanta_erro(
    async_db_session: AsyncSession,
):
    user_role = UserRolesFactory.create()
    await async_db_session.flush()

    schema_patch = schema.PatchUserRoles(user_id=uuid4(), role_id=uuid4())
    with pytest.raises(error.ValidationException) as exc_info:
        await UserRolesService.patch_user_role(
            user_role.id, schema_patch, async_db_session
        )

    errors = exc_info.value.detail
    assert len(errors) == 2


@pytest.mark.asyncio
async def test_patch_user_role_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    schema_patch = schema.PatchUserRoles(user_id=uuid4(), role_id=uuid4())

    with pytest.raises(error.CustomException) as exc_info:
        await UserRolesService.patch_user_role(
            uuid4(), schema_patch, async_db_session
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_role_com_sucesso(async_db_session: AsyncSession):
    user_role = UserRolesFactory.create()

    await async_db_session.flush()
    ur_id = user_role.id

    await UserRolesService.delete_user_role(ur_id, async_db_session)

    # Verifica exclusão real
    assert await async_db_session.get(UserRoles, ur_id) is None


@pytest.mark.asyncio
async def test_delete_user_role_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    with pytest.raises(error.CustomException) as exc_info:
        await UserRolesService.delete_user_role(uuid4(), async_db_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_roles_paginado(async_db_session: AsyncSession):
    UserRolesFactory.build_batch(2)
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
    result = await UserRolesService.get_user_roles(qp, async_db_session)

    assert result is not None
    # Depending on the generic implementation, it might be a dict or a Schema object
    if isinstance(result, dict):
        assert "data" in result or "items" in result
    else:
        assert hasattr(result, "data") or hasattr(result, "items")
