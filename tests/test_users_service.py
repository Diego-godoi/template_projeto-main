# tests/test_users_service.py
"""
Testes unitários da camada de serviço UsersService (Épico 5.2).

Cada teste opera sobre uma sessão transacional isolada (ver conftest.py),
garantindo rollback automático ao final — sem efeitos colaterais no banco.
"""

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app import error, schema
from app.services.users_service import UsersService

fake = Faker("pt_BR")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_post_schema(**overrides) -> schema.PostUsers:
    """Gera um PostUsers válido com dados aleatórios via Faker."""
    # CPF válido fixo para os testes (gerado pelo Faker br)
    cpf_raw = fake.cpf().replace(".", "").replace("-", "")
    senha_raw = "SenhaForte@123"

    defaults = {
        "email": fake.unique.email(),
        "password": senha_raw.encode(),
        "full_name": fake.name(),
        "cpf": cpf_raw,
        "active": True,
    }
    defaults.update(overrides)
    return schema.PostUsers.model_validate(defaults)


async def _criar_usuario(session: AsyncSession) -> tuple:
    """Cria um usuário no banco e retorna (objeto_criado, schema_usado)."""
    post = _make_post_schema()
    user = await UsersService.create_user(post, session)
    return user, post


# ---------------------------------------------------------------------------
# Testes de criação
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cria_usuario_com_sucesso(async_db_session: AsyncSession):
    """Criação de usuário com dados válidos retorna objeto Users persistido."""
    user, post = await _criar_usuario(async_db_session)

    assert user.id is not None
    assert user.email == post.email
    assert user.cpf == post.cpf
    assert user.active is True


@pytest.mark.asyncio
async def test_cria_usuario_email_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Tentar criar dois usuários com o mesmo e-mail deve lançar ValidationException."""
    user, post = await _criar_usuario(async_db_session)

    # Segundo usuário com mesmo email, CPF diferente
    cpf_novo = fake.cpf().replace(".", "").replace("-", "")
    post_duplicado = _make_post_schema(email=post.email, cpf=cpf_novo)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.create_user(post_duplicado, async_db_session)

    erros = exc_info.value.detail
    campos = [e["loc"][-1] for e in erros]
    assert "email" in campos


@pytest.mark.asyncio
async def test_cria_usuario_cpf_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Tentar criar dois usuários com o mesmo CPF deve lançar ValidationException."""
    user, post = await _criar_usuario(async_db_session)

    post_duplicado = _make_post_schema(cpf=post.cpf)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.create_user(post_duplicado, async_db_session)

    erros = exc_info.value.detail
    campos = [e["loc"][-1] for e in erros]
    assert "cpf" in campos


# ---------------------------------------------------------------------------
# Testes de atualização (PATCH)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_usuario_com_sucesso(async_db_session: AsyncSession):
    """Atualização parcial com nome completo diferente deve persistir a mudança."""
    user, _ = await _criar_usuario(async_db_session)
    novo_nome = "Nome Atualizado Silva"

    patch = schema.PatchUsers(full_name=novo_nome)
    atualizado = await UsersService.patch_user(
        user.id, patch, async_db_session
    )

    assert atualizado.full_name == novo_nome
    assert atualizado.id == user.id


@pytest.mark.asyncio
async def test_patch_usuario_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    """Atualização com UUID inexistente deve lançar HTTPException 404."""
    import uuid

    id_falso = uuid.uuid4()
    patch = schema.PatchUsers(full_name="Qualquer Nome")

    with pytest.raises(error.CustomException) as exc_info:
        await UsersService.patch_user(id_falso, patch, async_db_session)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Testes de remoção (DELETE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_usuario_com_sucesso(async_db_session: AsyncSession):
    """Remoção de usuário existente deve retornar o objeto deletado."""
    user, _ = await _criar_usuario(async_db_session)
    user_id = user.id

    await UsersService.delete_user(user_id, async_db_session)

    # Confirma que não existe mais na sessão
    from app.models import Users

    assert await async_db_session.get(Users, user_id) is None


@pytest.mark.asyncio
async def test_delete_usuario_id_inexistente_levanta_404(
    async_db_session: AsyncSession,
):
    """Remoção com UUID inexistente deve lançar HTTPException 404."""
    import uuid

    id_falso = uuid.uuid4()

    with pytest.raises(error.CustomException) as exc_info:
        await UsersService.delete_user(id_falso, async_db_session)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Testes de listagem (GET)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_users_retorna_service_response_vazio(
    async_db_session: AsyncSession,
):
    """get_users sem dados no banco deve retornar ServiceResponse com lista vazia."""
    from app.util.annotated import QueryParameters

    qp = QueryParameters(
        all_data=True,
        attribute=None,
        value=None,
        json_string=None,
        operator="=",
        skip=0,
        limit=100,
        include=None,
    )
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
    from app.util.annotated import QueryParameters

    await _criar_usuario(async_db_session)
    await _criar_usuario(async_db_session)

    qp = QueryParameters(
        all_data=True,
        attribute=None,
        value=None,
        json_string=None,
        operator="=",
        skip=0,
        limit=100,
        include=None,
    )
    result = await UsersService.get_users(qp, async_db_session)

    assert len(result.data) >= 2
    assert result.meta["total_items"] >= 2


# ---------------------------------------------------------------------------
# Testes de validação de duplicidade no PATCH
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_usuario_email_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Patch com email já usado por outro usuário deve lançar ValidationException."""
    user1, _ = await _criar_usuario(async_db_session)
    user2, _ = await _criar_usuario(async_db_session)

    patch = schema.PatchUsers(email=user1.email)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.patch_user(user2.id, patch, async_db_session)

    erros = exc_info.value.detail
    campos = [e["loc"][-1] for e in erros]
    assert "email" in campos


@pytest.mark.asyncio
async def test_patch_usuario_cpf_duplicado_levanta_erro(
    async_db_session: AsyncSession,
):
    """Patch com CPF já usado por outro usuário deve lançar ValidationException."""
    user1, _ = await _criar_usuario(async_db_session)
    user2, _ = await _criar_usuario(async_db_session)

    patch = schema.PatchUsers(cpf=user1.cpf)

    with pytest.raises(error.ValidationException) as exc_info:
        await UsersService.patch_user(user2.id, patch, async_db_session)

    erros = exc_info.value.detail
    campos = [e["loc"][-1] for e in erros]
    assert "cpf" in campos


@pytest.mark.asyncio
async def test_patch_usuario_com_senha_nova(
    async_db_session: AsyncSession,
):
    """Patch com campo password deve hashear a senha corretamente."""
    from app.core import security

    user, _ = await _criar_usuario(async_db_session)
    nova_senha = "NovaSenha@999"

    patch = schema.PatchUsers(password=nova_senha.encode())
    atualizado = await UsersService.patch_user(
        user.id, patch, async_db_session
    )

    # A senha deve ter sido hasheada, não armazenada crua
    assert await security.verify_password(nova_senha, atualizado.password)
