from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import error, schema
from app.models import Roles
from app.services.roles_service import RolesService
from app.util.annotated import QueryParameters

from .factories import RolesFactory


@pytest.mark.asyncio
async def test_create_role_com_sucesso(async_db_session: AsyncSession):
    role_payload = schema.PostRoles(
        name="Vendedor", description="Descrição do vendedor"
    )
    result = await RolesService.create_role(role_payload, async_db_session)
    assert result.id is not None
    assert result.name == "Vendedor"


@pytest.mark.asyncio
async def test_create_role_nome_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    RolesFactory.create(name="Gerente")
    await async_db_session.flush()

    schema_duplicado = schema.PostRoles(
        name="Gerente", description="Descrição"
    )
    with pytest.raises(error.ValidationException) as exc_info:
        await RolesService.create_role(schema_duplicado, async_db_session)

    errors = exc_info.value.detail
    # Verifica que o erro levantado avisa que nome já está cadastrado
    assert any("já está cadastrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_role_com_sucesso(async_db_session: AsyncSession):
    role = RolesFactory.create(name="Supervisor")
    await async_db_session.flush()

    schema_patch = schema.PatchRoles(name=None, description="Nova desc")
    role_atualizada = await RolesService.patch_role(
        role.id, schema_patch, async_db_session
    )

    assert role_atualizada.description == "Nova desc"
    assert role_atualizada.name == "Supervisor"  # Não alterado


@pytest.mark.asyncio
async def test_patch_role_nome_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    RolesFactory.create(name="Role1")
    role2 = RolesFactory.create(name="Role2")
    await async_db_session.flush()

    schema_patch = schema.PatchRoles(name="Role1")
    with pytest.raises(error.ValidationException) as exc_info:
        await RolesService.patch_role(role2.id, schema_patch, async_db_session)

    errors = exc_info.value.detail
    assert any("já está cadastrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_role_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    schema_patch = schema.PatchRoles(name="RoleFantasma")
    with pytest.raises(error.CustomException) as exc_info:
        await RolesService.patch_role(uuid4(), schema_patch, async_db_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_role_com_sucesso(async_db_session: AsyncSession):
    role = RolesFactory.create(name="Temporario")
    await async_db_session.flush()
    role_id = role.id

    await RolesService.delete_role(role_id, async_db_session)
    assert await async_db_session.get(Roles, role_id) is None


@pytest.mark.asyncio
async def test_delete_role_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    with pytest.raises(error.CustomException) as exc_info:
        await RolesService.delete_role(uuid4(), async_db_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_roles_paginado(async_db_session: AsyncSession):
    RolesFactory.create(name="List_Role_1")
    RolesFactory.create(name="List_Role_2")
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
    result = await RolesService.get_roles(qp, async_db_session)

    assert result is not None
    if isinstance(result, dict):
        assert "data" in result or "items" in result
    else:
        assert hasattr(result, "data") or hasattr(result, "items")
