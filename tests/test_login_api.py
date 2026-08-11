import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import core
from app.core import security

from .factories import UsersFactory


@pytest.mark.asyncio
async def test_post_login_success(client, async_db_session: AsyncSession):
    raw_password = "SenhaForte@123"
    hashed_password = await core.get_password_hash(raw_password)

    user = UsersFactory.create(password=hashed_password, active=True)
    await async_db_session.flush()

    response = await client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": raw_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_login_credenciais_incorretas(
    client, async_db_session: AsyncSession
):
    raw_password = "SenhaForte@123"
    hashed_password = await core.get_password_hash(raw_password)

    user = UsersFactory.create(password=hashed_password)
    await async_db_session.flush()

    response = await client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": "senhaincorreta"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code in [400, 401, 422]


@pytest.mark.asyncio
async def test_forgot_my_password_retorna_mensagens_iguais_para_impedir_enum_de_emails(
    client, async_db_session: AsyncSession
):
    from unittest.mock import patch

    with patch("app.util.send_email") as mock_send:
        user = UsersFactory.create()
        await async_db_session.flush()

        # 1. Envia com email EXISTENTE
        response_existente = await client.post(
            "/api/v1/forgot-my-password/", json={"email": user.email}
        )

        assert response_existente.status_code == 200
        assert (
            "instruções serão enviadas" in response_existente.json()["message"]
        )

        # O user ganha um código de redefinição
        await async_db_session.refresh(user)
        assert user.reset_password_code is not None
        assert user.reset_password_expiration is not None

        # 2. Envia com email INEXISTENTE
        response_fake = await client.post(
            "/api/v1/forgot-my-password/",
            json={"email": "nao_cadastrado@teste.com"},
        )

        assert response_fake.status_code == 200
        assert "instruções serão enviadas" in response_fake.json()["message"]

        # Garante que o e-mail foi "enviado" apenas para o usuário que existe
        assert mock_send.call_count == 1


@pytest.mark.asyncio
async def test_new_password_com_sucesso_e_expiracao(
    client, async_db_session: AsyncSession
):
    from datetime import datetime, timedelta, timezone

    user = UsersFactory.create()
    await async_db_session.flush()
    code = "ABC123Z"
    hash_code = await security.get_password_hash(code)

    # Força validade futura
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now(timezone.utc) + timedelta(
        minutes=15
    )
    await async_db_session.flush()

    # Tenta resetar
    new_pass = "NovaSenhaSegura123"
    response = await client.put(
        "/api/v1/new-password/",
        json={"email": user.email, "code": code, "password": new_pass},
    )

    assert response.status_code == 200
    assert response.json() == "Senha alterada"

    # Confirma que token resetou e nova hash funciona
    await async_db_session.refresh(user)
    assert user.reset_password_code is None
    assert await security.verify_password(new_pass, user.password) is True

    # ----
    # Cenário 2: Forçando Código Expirado
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now(timezone.utc) - timedelta(
        minutes=15
    )
    await async_db_session.flush()

    response_expr = await client.put(
        "/api/v1/new-password/",
        json={"email": user.email, "code": code, "password": new_pass},
    )

    assert response_expr.status_code == 401
    assert "Código expirado" in response_expr.json()["detail"]


@pytest.mark.asyncio
async def test_new_password_com_codigo_invalido(
    client, async_db_session: AsyncSession
):
    from datetime import datetime, timedelta, timezone

    user = UsersFactory.create()
    await async_db_session.flush()
    code = "ABC123Z"
    hash_code = await security.get_password_hash(code)

    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now(timezone.utc) + timedelta(
        minutes=15
    )
    await async_db_session.flush()

    response = await client.put(
        "/api/v1/new-password/",
        json={
            "email": user.email,
            "code": "ERRADO",
            "password": "NovaSenhaSegura",
        },
    )

    assert response.status_code == 401
    assert "Email ou código" in response.json()["detail"]
