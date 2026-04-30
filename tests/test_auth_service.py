# tests/test_auth_service.py
"""
Testes unitários da camada de serviço AuthService.

Cobre os caminhos de login, reset de senha e edge cases de validação,
operando sobre sessão transacional isolada (conftest.py).
"""

from datetime import datetime, timedelta

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app import core, error, models, schema
from app.services.auth_service import AuthService

fake = Faker("pt_BR")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _criar_usuario_com_senha(
    session: AsyncSession,
    password: str = "SenhaForte@123",
    active: bool = True,
) -> tuple[models.Users, str]:
    """Cria um usuário com senha conhecida para testes de login."""
    from app.services.users_service import UsersService
    from tests.test_users_service import _make_post_schema

    post = _make_post_schema(active=active)
    user = await UsersService.create_user(post, session)
    # A senha crua é sempre "SenhaForte@123" do _make_post_schema
    return user, password


# ---------------------------------------------------------------------------
# Testes de Login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_com_sucesso(async_db_session: AsyncSession):
    """Login com credenciais válidas deve retornar (user, sub)."""
    user, senha = await _criar_usuario_com_senha(async_db_session)

    result_user, sub = await AuthService.login(
        user.email, senha, async_db_session
    )

    assert result_user.id == user.id
    assert sub["user_id"] == str(user.id)
    assert isinstance(sub["scopes"], list)


@pytest.mark.asyncio
async def test_login_username_vazio_levanta_400(
    async_db_session: AsyncSession,
):
    """Login com username vazio/None deve lançar CustomException 400."""
    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.login("", "qualquer", async_db_session)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_login_email_inexistente_levanta_400(
    async_db_session: AsyncSession,
):
    """Login com email não cadastrado deve lançar CustomException 400."""
    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.login(
            "naoexiste@teste.com", "SenhaForte@123", async_db_session
        )

    assert exc_info.value.status_code == 400
    assert "Email ou Senha" in exc_info.value.detail


@pytest.mark.asyncio
async def test_login_senha_incorreta_levanta_400(
    async_db_session: AsyncSession,
):
    """Login com senha incorreta deve lançar CustomException 400."""
    user, _ = await _criar_usuario_com_senha(async_db_session)

    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.login(user.email, "SenhaErrada999", async_db_session)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_login_usuario_inativo_levanta_401(
    async_db_session: AsyncSession,
):
    """Login de usuário inativo deve lançar CustomException 401."""
    user, senha = await _criar_usuario_com_senha(
        async_db_session, active=False
    )
    # Forçar inativo caso o schema não respeite
    user.active = False
    async_db_session.add(user)
    await async_db_session.commit()

    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.login(user.email, senha, async_db_session)

    assert exc_info.value.status_code == 401
    assert "Inativo" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Testes de Reset de Senha
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_password_reset_usuario_inexistente_retorna_mensagem_generica(
    async_db_session: AsyncSession,
):
    """Requisitar reset para email inexistente deve retornar mensagem sem vazar info."""
    message, email_payload = await AuthService.request_password_reset(
        "inexistente@teste.com", async_db_session
    )

    assert "instruções serão enviadas" in message
    assert email_payload is None


@pytest.mark.asyncio
async def test_request_password_reset_usuario_existente_gera_codigo(
    async_db_session: AsyncSession,
):
    """Requisitar reset para email existente deve persistir código e retornar payload."""
    from unittest.mock import patch

    user, _ = await _criar_usuario_com_senha(async_db_session)

    with patch(
        "app.services.auth_service.util.template_string",
        return_value="<html>mock</html>",
    ):
        message, email_payload = await AuthService.request_password_reset(
            user.email, async_db_session
        )

    assert "instruções serão enviadas" in message
    assert email_payload is not None
    to, subject, body = email_payload
    assert to == user.email

    await async_db_session.refresh(user)
    assert user.reset_password_code is not None
    assert user.reset_password_expiration is not None


@pytest.mark.asyncio
async def test_reset_password_com_sucesso(async_db_session: AsyncSession):
    """Reset de senha com código válido deve alterar a senha."""
    user, _ = await _criar_usuario_com_senha(async_db_session)

    code = "AB1234"
    hash_code = await core.get_password_hash(code)
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now() + timedelta(minutes=15)
    async_db_session.add(user)
    await async_db_session.commit()

    data = schema.ResetPassword(
        email=user.email, code=code, password="NovaSenha@456"
    )
    result = await AuthService.reset_password(data, async_db_session)

    assert result == "Senha alterada"
    await async_db_session.refresh(user)
    assert user.reset_password_code is None
    assert await core.verify_password("NovaSenha@456", user.password)


@pytest.mark.asyncio
async def test_reset_password_usuario_inexistente_levanta_401(
    async_db_session: AsyncSession,
):
    """Reset com email inexistente deve lançar 401."""
    data = schema.ResetPassword(
        email="fantasma@teste.com", code="AB1234", password="NovaSenha@456"
    )

    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.reset_password(data, async_db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_reset_password_codigo_expirado_levanta_401(
    async_db_session: AsyncSession,
):
    """Reset com código expirado deve lançar 401."""
    user, _ = await _criar_usuario_com_senha(async_db_session)

    code = "AB1234"
    hash_code = await core.get_password_hash(code)
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now() - timedelta(minutes=15)
    async_db_session.add(user)
    await async_db_session.commit()

    data = schema.ResetPassword(
        email=user.email, code=code, password="NovaSenha@456"
    )

    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.reset_password(data, async_db_session)

    assert exc_info.value.status_code == 401
    assert "expirado" in exc_info.value.detail


@pytest.mark.asyncio
async def test_reset_password_codigo_incorreto_levanta_401(
    async_db_session: AsyncSession,
):
    """Reset com código incorreto deve lançar 401."""
    user, _ = await _criar_usuario_com_senha(async_db_session)

    code = "AB1234"
    hash_code = await core.get_password_hash(code)
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now() + timedelta(minutes=15)
    async_db_session.add(user)
    await async_db_session.commit()

    data = schema.ResetPassword(
        email=user.email, code="ERRADO", password="NovaSenha@456"
    )

    with pytest.raises(error.CustomException) as exc_info:
        await AuthService.reset_password(data, async_db_session)

    assert exc_info.value.status_code == 401
    assert "código inválido" in exc_info.value.detail
