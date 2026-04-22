import pytest

from app.core import security
from app.models import Users
from tests.test_users_service import _criar_usuario


def test_post_login_success(client, db_session):
    user, post = _criar_usuario(db_session)

    response = client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": "SenhaForte@123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


def test_post_login_credenciais_incorretas(client, db_session):
    user, post = _criar_usuario(db_session)

    response = client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": "senhaincorreta"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Dependendo da implementação do `models.Users.login` isso lançará ValidationError ou CustomException(401)
    assert response.status_code in [400, 401, 422]


def test_forgot_my_password_retorna_mensagens_iguais_para_impedir_enum_de_emails(
    client, db_session
):
    user, _ = _criar_usuario(db_session)

    # 1. Envia com email EXISTENTE
    response_existente = client.post(
        "/api/v1/forgot-my-password/", json={"email": user.email}
    )

    assert response_existente.status_code == 200
    assert "instruções serão enviadas" in response_existente.json()["message"]

    # O user ganha um código de redefinição
    db_session.refresh(user)
    assert user.reset_password_code is not None
    assert user.reset_password_expiration is not None

    # 2. Envia com email INEXISTENTE
    response_fake = client.post(
        "/api/v1/forgot-my-password/",
        json={"email": "nao_cadastrado@teste.com"},
    )

    assert response_fake.status_code == 200
    assert "instruções serão enviadas" in response_fake.json()["message"]


def test_new_password_com_sucesso_e_expiracao(client, db_session):
    from datetime import datetime, timedelta

    user, _ = _criar_usuario(db_session)
    code = "ABC123Z"
    hash_code = security.get_password_hash(code)

    # Força validade futura
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now() + timedelta(minutes=15)
    db_session.flush()

    # Tenta resetar
    new_pass = "NovaSenhaSegura123"
    response = client.put(
        "/api/v1/new-password/",
        json={"email": user.email, "code": code, "password": new_pass},
    )

    assert response.status_code == 200
    assert response.json() == "Senha alterada"

    # Confirma que token resetou e nova hash funciona
    db_session.refresh(user)
    assert user.reset_password_code is None
    assert security.verify_password(new_pass, user.password) is True

    # ----
    # Cenário 2: Forçando Código Expirado
    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now() - timedelta(minutes=15)
    db_session.flush()

    response_expr = client.put(
        "/api/v1/new-password/",
        json={"email": user.email, "code": code, "password": new_pass},
    )

    assert response_expr.status_code == 401
    assert "Código expirado" in response_expr.json()["detail"]


def test_new_password_com_codigo_invalido(client, db_session):
    from datetime import datetime, timedelta

    user, _ = _criar_usuario(db_session)
    code = "ABC123Z"
    hash_code = security.get_password_hash(code)

    user.reset_password_code = hash_code
    user.reset_password_expiration = datetime.now() + timedelta(minutes=15)
    db_session.flush()

    response = client.put(
        "/api/v1/new-password/",
        json={
            "email": user.email,
            "code": "ERRADO",
            "password": "NovaSenhaSegura",
        },
    )

    assert response.status_code == 401
    assert "Email ou código" in response.json()["detail"]
