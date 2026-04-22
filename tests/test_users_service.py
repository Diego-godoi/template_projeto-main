# tests/test_users_service.py
"""
Testes unitários da camada de serviço UsersService (Épico 5.2).

Cada teste opera sobre uma sessão transacional isolada (ver conftest.py),
garantindo rollback automático ao final — sem efeitos colaterais no banco.
"""

import pytest
from faker import Faker
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import schema
from app.error import ValidationException
from app.services.users_service import UsersService
from app.util import normalize_password

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
        "password": senha_raw.encode(),  # será hasheado pelo model_validator
        "full_name": fake.name(),
        "cpf": cpf_raw,
        "active": True,
    }
    defaults.update(overrides)
    return schema.PostUsers(**defaults)


def _criar_usuario(session: Session) -> tuple:
    """Cria um usuário no banco e retorna (objeto_criado, schema_usado)."""
    post = _make_post_schema()
    user = UsersService.create_user(post, session)
    return user, post


# ---------------------------------------------------------------------------
# Testes de criação
# ---------------------------------------------------------------------------


def test_cria_usuario_com_sucesso(db_session: Session):
    """Criação de usuário com dados válidos retorna objeto Users persistido."""
    user, post = _criar_usuario(db_session)

    assert user.id is not None
    assert user.email == post.email
    assert user.cpf == post.cpf
    assert user.active is True


def test_cria_usuario_email_duplicado_levanta_erro(db_session: Session):
    """Tentar criar dois usuários com o mesmo e-mail deve lançar ValidationException."""
    user, post = _criar_usuario(db_session)

    # Segundo usuário com mesmo email, CPF diferente
    cpf_novo = fake.cpf().replace(".", "").replace("-", "")
    post_duplicado = _make_post_schema(email=post.email, cpf=cpf_novo)

    with pytest.raises(ValidationException) as exc_info:
        UsersService.create_user(post_duplicado, db_session)

    erros = exc_info.value.detail
    campos = [e["loc"][-1] for e in erros]
    assert "email" in campos


def test_cria_usuario_cpf_duplicado_levanta_erro(db_session: Session):
    """Tentar criar dois usuários com o mesmo CPF deve lançar ValidationException."""
    user, post = _criar_usuario(db_session)

    post_duplicado = _make_post_schema(cpf=post.cpf)

    with pytest.raises(ValidationException) as exc_info:
        UsersService.create_user(post_duplicado, db_session)

    erros = exc_info.value.detail
    campos = [e["loc"][-1] for e in erros]
    assert "cpf" in campos


# ---------------------------------------------------------------------------
# Testes de atualização (PATCH)
# ---------------------------------------------------------------------------


def test_patch_usuario_com_sucesso(db_session: Session):
    """Atualização parcial com nome completo diferente deve persistir a mudança."""
    user, _ = _criar_usuario(db_session)
    novo_nome = "Nome Atualizado Silva"

    patch = schema.PatchUsers(full_name=novo_nome)
    atualizado = UsersService.patch_user(user.id, patch, db_session)

    assert atualizado.full_name == novo_nome
    assert atualizado.id == user.id


def test_patch_usuario_id_inexistente_levanta_404(db_session: Session):
    """Atualização com UUID inexistente deve lançar HTTPException 404."""
    import uuid

    id_falso = uuid.uuid4()
    patch = schema.PatchUsers(full_name="Qualquer Nome")

    with pytest.raises(HTTPException) as exc_info:
        UsersService.patch_user(id_falso, patch, db_session)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Testes de remoção (DELETE)
# ---------------------------------------------------------------------------


def test_delete_usuario_com_sucesso(db_session: Session):
    """Remoção de usuário existente deve retornar o objeto deletado."""
    user, _ = _criar_usuario(db_session)
    user_id = user.id

    UsersService.delete_user(user_id, db_session)

    # Confirma que não existe mais na sessão
    assert db_session.get(type(user), user_id) is None


def test_delete_usuario_id_inexistente_levanta_404(db_session: Session):
    """Remoção com UUID inexistente deve lançar HTTPException 404."""
    import uuid

    id_falso = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        UsersService.delete_user(id_falso, db_session)

    assert exc_info.value.status_code == 404
