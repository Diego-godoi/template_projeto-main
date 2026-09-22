from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import error
from app.auth import auth
from app.core import security

from .factories import RolesFactory, UserRolesFactory, UsersFactory

# ==========================================
# Testes Security (Bcrypt)
# ==========================================


@pytest.mark.asyncio
async def test_password_hash_and_verify():
    plain_password = "MinhaSenhaSuperSecreta"

    # 1. Hasheia a senha
    hashed = await security.get_password_hash(plain_password)
    assert hashed != plain_password
    assert isinstance(hashed, bytes)

    # 2. Verifica sucesso de match
    assert await security.verify_password(plain_password, hashed) is True

    # 3. Verifica falha de match
    assert await security.verify_password("SenhaErrada", hashed) is False


@pytest.mark.asyncio
async def test_verify_password_bytes_support():
    plain_password = b"SenhaBytes"
    hashed = await security.get_password_hash(plain_password)

    # Valida match mesmo que o plain_password seja mantido em bytes
    assert await security.verify_password(plain_password, hashed) is True


@pytest.mark.asyncio
@patch("app.core.security.bcrypt.checkpw")
async def test_verify_password_lanca_excecao_interna(mock_checkpw):
    """Garante que falhas obscuras da lib disparem 500 sem vazar stack trace."""
    mock_checkpw.side_effect = ValueError("Lib error")
    with pytest.raises(error.CustomException) as exc:
        await security.verify_password("senha", b"hash")

    assert exc.value.status_code == 500
    assert "Erro Interno" in exc.value.detail


@pytest.mark.asyncio
@patch("app.core.security.bcrypt.hashpw")
async def test_get_password_hash_lanca_excecao_interna(mock_hashpw):
    mock_hashpw.side_effect = ValueError("Lib error hash")
    with pytest.raises(error.CustomException) as exc:
        await security.get_password_hash("senha")

    assert exc.value.status_code == 500


# ==========================================
# Testes Auth (JWT Tokens)
# ==========================================


@pytest.mark.asyncio
async def test_encode_and_decode_token(async_db_session: AsyncSession):
    user = UsersFactory.create(is_deleted=False)
    role = RolesFactory.create(name="User")
    UserRolesFactory.create(user=user, role=role)
    await async_db_session.flush()

    user_id = str(user.id)
    token = auth.encode_token({"sub": user_id, "roles": ["User"]}, exp=15)
    assert isinstance(token, str)

    decoded = await auth.decode_token(token, async_db_session)

    assert decoded["sub"] == user_id
    assert decoded["roles"] == ["user"]


@pytest.mark.asyncio
async def test_decode_token_expirado(async_db_session: AsyncSession):
    # Gerando um token que expirou no passado
    sub = {"user_id": "fake_id"}
    token = auth.encode_token(sub, exp=-15)  # Expirou há 15 minutos

    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(token, async_db_session)

    assert exc.value.status_code == 401
    assert "token expirou" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_decode_token_invalido(async_db_session: AsyncSession):
    valueless_token = "eyabc.invalido.123"

    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(valueless_token, async_db_session)

    assert exc.value.status_code == 401
    assert "token é inválido" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_decode_token_usuario_desativado_ou_nao_encontrado(
    async_db_session: AsyncSession,
):
    # Passa um ID de usuário que não tem cadastro
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    sub = {"user_id": fake_uuid}
    token = auth.encode_token(sub, exp=15)

    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(token, async_db_session)

    assert exc.value.status_code == 401
    assert "usuário não encontrado" in exc.value.detail.lower()
