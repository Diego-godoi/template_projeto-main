from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import error
from app.models import Roles
from app.schema import PatchRoles, PostRoles
from app.services.roles_service import RolesService
from app.util.annotated import QueryParameters


async def _criar_role(db_session: AsyncSession, name="Admin") -> Roles:
    """Fixture auxiliar para criar um papel direto pelo Service."""
    # O schema aplica capitalização automática (ex: user -> User)
    from app import util

    normalized_name = util.normalize_capitalize(name)
    schema = PostRoles(name=name)
    # Tenta resgatar se já existe no banco temporal para não violar DB durante tests massivos
    stmt = select(Roles).where(Roles.name == normalized_name)
    existing = (await db_session.execute(stmt)).scalars().first()
    if existing:
        return existing

    return await RolesService.create_role(schema, db_session)


@pytest.mark.asyncio
async def test_create_role_com_sucesso(async_db_session: AsyncSession):
    role = await _criar_role(async_db_session, name="Vendedor")
    assert role.id is not None
    assert role.name == "Vendedor"


@pytest.mark.asyncio
async def test_create_role_nome_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    await _criar_role(async_db_session, name="Gerente")

    schema_duplicado = PostRoles(name="Gerente")
    with pytest.raises(error.ValidationException) as exc_info:
        await RolesService.create_role(schema_duplicado, async_db_session)

    errors = exc_info.value.detail
    # Verifica que o erro levantado avisa que nome já está cadastrado
    assert any("já está cadastrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_role_com_sucesso(async_db_session: AsyncSession):
    role = await _criar_role(async_db_session, name="Supervisor")

    schema_patch = PatchRoles(description="Nova desc")
    role_atualizada = await RolesService.patch_role(
        role.id, schema_patch, async_db_session
    )

    assert role_atualizada.description == "Nova desc"
    assert role_atualizada.name == "Supervisor"  # Não alterado


@pytest.mark.asyncio
async def test_patch_role_nome_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    role1 = await _criar_role(async_db_session, name="Role1")
    role2 = await _criar_role(async_db_session, name="Role2")

    # Tenta atualizar role2 para ter o nome da role1
    schema_patch = PatchRoles(name="Role1")
    with pytest.raises(error.ValidationException) as exc_info:
        await RolesService.patch_role(role2.id, schema_patch, async_db_session)

    errors = exc_info.value.detail
    assert any("já está cadastrado" in err["msg"] for err in errors)


@pytest.mark.asyncio
async def test_patch_role_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    schema_patch = PatchRoles(name="RoleFantasma")
    with pytest.raises(error.CustomException) as exc_info:
        await RolesService.patch_role(uuid4(), schema_patch, async_db_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_role_com_sucesso(async_db_session: AsyncSession):
    role = await _criar_role(async_db_session, name="Temporario")
    role_id = role.id

    await RolesService.delete_role(role_id, async_db_session)

    # Confirma exclusão na sessão
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
    await _criar_role(async_db_session, name="List_Role_1")
    await _criar_role(async_db_session, name="List_Role_2")

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
