from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import error
from app.auth import auth
from app.core import security

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

    # Valida match mesmo que o plain_password seja mantido em bytes (a doc do security permite)
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
    from tests.test_user_roles_service import _criar_user_role

    # Cria user dummy para validação de integridade do payload
    user_role = await _criar_user_role(async_db_session)
    user_id = str(user_role.user_id)
    sub = {"user_id": user_id}

    # Encode token
    token = auth.encode_token(sub, exp=15)
    assert isinstance(token, str)

    # Decode Token
    decoded = await auth.decode_token(token, async_db_session)

    assert "user_id" in decoded
    assert decoded["user_id"] == user_id
    assert decoded["scopes"] == ["user"]


@pytest.mark.asyncio
async def test_decode_token_expirado(async_db_session: AsyncSession):
    # Gerando um token que espirou no passado
    sub = '{"user_id": "fake_id"}'
    token = auth.encode_token(sub, exp=-15)  # Expirou a 15 minutos

    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(token, async_db_session)

    assert exc.value.status_code == 401
    assert "token expirou" in exc.value.detail


@pytest.mark.asyncio
async def test_decode_token_invalido(async_db_session: AsyncSession):
    valueless_token = "eyabc.invalido.123"

    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(valueless_token, async_db_session)

    assert exc.value.status_code == 401
    assert "token é inválido" in exc.value.detail


@pytest.mark.asyncio
async def test_decode_token_usuario_desativado_ou_nao_encontrado(
    async_db_session: AsyncSession,
):
    # Passa um ID de usuário que não tem cadastro (não gerado nas fixtures local)
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    sub = {"user_id": fake_uuid}
    token = auth.encode_token(sub, exp=15)

    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(token, async_db_session)

    assert exc.value.status_code == 401
    assert "usuário não encontrado" in exc.value.detail


@pytest.mark.asyncio
async def test_decode_token_restricao_de_scopes(
    async_db_session: AsyncSession,
):
    from app.models import UserRoles
    from tests.test_roles_service import _criar_role
    from tests.test_users_service import _criar_usuario

    user, _ = await _criar_usuario(async_db_session)
    role_user = await _criar_role(async_db_session, name="user")
    role_manager = await _criar_role(async_db_session, name="manager")

    user.user_roles.append(UserRoles(role_id=str(role_user.id)))
    user.user_roles.append(UserRoles(role_id=str(role_manager.id)))
    await async_db_session.commit()

    token = auth.encode_token({"user_id": str(user.id)}, exp=15)

    # Deve permitir user e manager
    decoded_user = await auth.decode_token(
        token, async_db_session, scopes=["user"]
    )
    assert decoded_user["user_id"] == str(user.id)
    assert "user" in decoded_user["scopes"]

    decoded_manager = await auth.decode_token(
        token, async_db_session, scopes=["manager"]
    )
    assert "manager" in decoded_manager["scopes"]

    # Não deve permitir admin
    with pytest.raises(error.CustomException) as exc:
        await auth.decode_token(token, async_db_session, scopes=["admin"])

    assert exc.value.status_code == 401
    assert "não tem permissão" in exc.value.detail
