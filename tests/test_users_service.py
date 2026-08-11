# tests/test_users_service.py
"""
Testes de integração da camada de serviço UsersService.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import error, models, schema
from app.services.users_service import UsersService
from app.util.annotated import QueryParameters
from tests.factories import (
    PatchUsersFactory,
    PostUsersFactory,
    UsersFactory,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_default_query_params(**overrides) -> QueryParameters:
    """Cria QueryParameters com valores padrão para listagem."""
    defaults = {
        "all_data": True,
        "attribute": None,
        "value": None,
        "json_string": None,
        "operator": "=",
        "skip": 0,
        "limit": 100,
        "include": None,
    }
    defaults.update(overrides)
    return QueryParameters(**defaults)


def _assert_validation_field(
    exc: error.ValidationException, *expected_fields: str
):
    """Verifica que a ValidationException contém erro para cada campo esperado."""
    campos = [e["loc"][-1] for e in exc.detail]
    for field in expected_fields:
        assert field in campos


async def _criar_usuario_via_service(
    session: AsyncSession, **post_overrides
) -> tuple[models.Users, schema.PostUsers]:
    """Cria um usuário passando pelo fluxo real de `UsersService.create_user`."""
    post = PostUsersFactory(**post_overrides)
    user = await UsersService.create_user(post, session)
    return user, post


# ===========================================================================
# TESTES DE CRIAÇÃO (CREATE)
# ===========================================================================


@pytest.mark.asyncio
async def test_cria_usuario_com_sucesso(async_db_session: AsyncSession):
    """Criação com dados válidos retorna objeto Users persistido."""
    user, post = await _criar_usuario_via_service(async_db_session)

    assert user.id is not None
    assert user.email == post.email
    assert user.cpf == post.cpf


@pytest.mark.asyncio
async def test_cria_usuario_email_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Tentar criar usuário com email já cadastrado deve lançar ValidationException."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    post_dup = PostUsersFactory(email=usuario.email)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.create_user(post_dup, async_db_session)

    _assert_validation_field(exc_info.value, "email")


@pytest.mark.asyncio
async def test_cria_usuario_cpf_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Tentar criar usuário com CPF já cadastrado deve lançar ValidationException."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    post_dup = PostUsersFactory(cpf=usuario.cpf)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.create_user(post_dup, async_db_session)

    _assert_validation_field(exc_info.value, "cpf")


@pytest.mark.asyncio
async def test_cria_usuario_email_e_cpf_duplicados_acumula_erros(
    async_db_session: AsyncSession,
):
    """Email E CPF duplicados devem retornar ambos os erros na mesma exceção."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    post_dup = PostUsersFactory(email=usuario.email, cpf=usuario.cpf)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.create_user(post_dup, async_db_session)

    _assert_validation_field(exc_info.value, "email", "cpf")


# ===========================================================================
# TESTES DE ATUALIZAÇÃO (PATCH)
# ===========================================================================


@pytest.mark.asyncio
async def test_patch_usuario_com_sucesso(
    async_db_session: AsyncSession,
):
    """Atualização parcial persiste as mudanças enviadas."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    patch_data = PatchUsersFactory()
    atualizado = await UsersService.patch_user(
        usuario.id, patch_data, async_db_session
    )

    assert atualizado.id == usuario.id
    assert atualizado.name == patch_data.name


@pytest.mark.asyncio
async def test_patch_usuario_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    """Atualização com UUID inexistente lança CustomException 404."""
    id_falso = uuid.uuid4()

    with pytest.raises(error.CustomException) as exc_info:
        await UsersService.patch_user(
            id_falso, PatchUsersFactory(), async_db_session
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_patch_usuario_email_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Patch com email já usado por outro usuário lança ValidationException."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    outro_usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    patch_data = schema.PatchUsers(email=outro_usuario.email)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.patch_user(usuario.id, patch_data, async_db_session)

    _assert_validation_field(exc_info.value, "email")


@pytest.mark.asyncio
async def test_patch_usuario_cpf_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Patch com CPF já usado por outro usuário lança ValidationException."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    outro_usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    patch_data = schema.PatchUsers(cpf=outro_usuario.cpf)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.patch_user(usuario.id, patch_data, async_db_session)

    _assert_validation_field(exc_info.value, "cpf")


@pytest.mark.asyncio
async def test_patch_usuario_email_proprio_nao_levanta_erro(
    async_db_session: AsyncSession,
):
    """Patch enviando o próprio email do usuário NÃO deve lançar erro."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    patch_data = schema.PatchUsers(email=usuario.email)
    atualizado = await UsersService.patch_user(
        usuario.id, patch_data, async_db_session
    )

    assert atualizado.email == usuario.email


@pytest.mark.asyncio
async def test_patch_usuario_cpf_proprio_nao_levanta_erro(
    async_db_session: AsyncSession,
):
    """Patch enviando o próprio CPF do usuário NÃO deve lançar erro."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    patch_data = schema.PatchUsers(cpf=usuario.cpf)
    atualizado = await UsersService.patch_user(
        usuario.id, patch_data, async_db_session
    )

    assert atualizado.cpf == usuario.cpf


@pytest.mark.asyncio
async def test_patch_usuario_com_senha_nova(
    async_db_session: AsyncSession,
):
    """Patch com campo password deve passar o hash pela função utilitária."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    nova_senha = "NovaSenha@999"
    patch_data = schema.PatchUsers(password=nova_senha)
    atualizado = await UsersService.patch_user(
        usuario.id, patch_data, async_db_session
    )

    assert atualizado.password != nova_senha


# ===========================================================================
# TESTES DE REMOÇÃO (DELETE)
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_usuario_sucesso(
    async_db_session: AsyncSession,
):
    """Remoção exclui o registro do banco de dados."""
    usuario: models.Users = UsersFactory.create()
    await async_db_session.flush()
    resultado = await UsersService.delete_user(usuario.id, async_db_session)

    assert resultado.id == usuario.id
    user_no_banco = await async_db_session.get(models.Users, usuario.id)
    assert user_no_banco is None


@pytest.mark.asyncio
async def test_delete_usuario_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    """Exclusão com UUID inexistente lança CustomException 404."""
    id_falso = uuid.uuid4()

    with pytest.raises(error.CustomException) as exc_info:
        await UsersService.delete_user(id_falso, async_db_session)

    assert exc_info.value.status_code == 404


# ===========================================================================
# TESTES DE LISTAGEM (GET)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_users_retorna_service_response_vazio(
    async_db_session: AsyncSession,
):
    """get_users sem dados no banco retorna ServiceResponse com lista vazia."""
    qp = _make_default_query_params()
    result = await UsersService.get_users(qp, async_db_session)

    assert hasattr(result, "data")
    assert hasattr(result, "meta")
    assert isinstance(result.data, list)
    assert result.meta["total_items"] >= 0


@pytest.mark.asyncio
async def test_get_users_retorna_usuarios_criados(
    async_db_session: AsyncSession,
):
    """get_users deve retornar os usuários previamente criados."""
    UsersFactory.create_batch(2)
    await async_db_session.flush()

    qp = _make_default_query_params()
    result = await UsersService.get_users(qp, async_db_session)

    assert len(result.data) >= 2
    assert result.meta["total_items"] >= 2


@pytest.mark.asyncio
async def test_get_users_retorna_meta_com_total(
    async_db_session: AsyncSession,
):
    """get_users retorna meta com total_items correto."""
    UsersFactory.create()
    await async_db_session.flush()
    qp = _make_default_query_params()
    result = await UsersService.get_users(qp, async_db_session)

    assert "total_items" in result.meta
    assert isinstance(result.meta["total_items"], int)
    assert result.meta["total_items"] >= 1
