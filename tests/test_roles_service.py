# tests/test_roles_service.py
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.error import ValidationException
from app.models import Roles
from app.schema import PatchRoles, PostRoles
from app.services.roles_service import RolesService
from app.util.annotated import QueryParameters


def _criar_role(db_session: Session, name="Admin", access_level=1) -> Roles:
    """Fixture auxiliar para criar um papel direto pelo Service."""
    schema = PostRoles(name=name, access_level=access_level)
    # Tenta resgatar se já existe no banco temporal para não violar DB durante tests massivos
    existing = Roles.get(_db=db_session, attribute="name", value=name)
    if existing:
        return existing

    return RolesService.create_role(schema, db_session)


def test_create_role_com_sucesso(db_session: Session):
    role = _criar_role(db_session, name="Vendedor", access_level=2)
    assert role.id is not None
    assert role.name == "Vendedor"
    assert role.access_level == 2


def test_create_role_nome_duplicado_levanta_erro(db_session: Session):
    _criar_role(db_session, name="Gerente")

    schema_duplicado = PostRoles(name="Gerente", access_level=3)
    with pytest.raises(ValidationException) as exc_info:
        RolesService.create_role(schema_duplicado, db_session)

    errors = exc_info.value.detail
    # Verifica que o erro levantado avisa que nome já está cadastrado
    assert any("já está cadastrado" in err["msg"] for err in errors)


def test_patch_role_com_sucesso(db_session: Session):
    role = _criar_role(db_session, name="Supervisor", access_level=4)

    schema_patch = PatchRoles(access_level=5)
    role_atualizada = RolesService.patch_role(role.id, schema_patch, db_session)

    assert role_atualizada.access_level == 5
    assert role_atualizada.name == "Supervisor"  # Não alterado


def test_patch_role_nome_duplicado_levanta_erro(db_session: Session):
    role1 = _criar_role(db_session, name="Role1")
    role2 = _criar_role(db_session, name="Role2")

    # Tenta atualizar role2 para ter o nome da role1
    schema_patch = PatchRoles(name="Role1")
    with pytest.raises(ValidationException) as exc_info:
        RolesService.patch_role(role2.id, schema_patch, db_session)

    errors = exc_info.value.detail
    assert any("já está cadastrado" in err["msg"] for err in errors)


def test_patch_role_id_inexistente_levanta_404(db_session: Session):
    schema_patch = PatchRoles(name="RoleFantasma")
    with pytest.raises(HTTPException) as exc_info:
        RolesService.patch_role(uuid4(), schema_patch, db_session)

    assert exc_info.value.status_code == 404


def test_delete_role_com_sucesso(db_session: Session):
    role = _criar_role(db_session, name="Temporario")
    role_id = role.id

    RolesService.delete_role(role_id, db_session)

    # Confirma exclusão na sessão
    assert db_session.get(Roles, role_id) is None


def test_delete_role_id_inexistente_levanta_404(db_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        RolesService.delete_role(uuid4(), db_session)

    assert exc_info.value.status_code == 404


def test_get_roles_paginado(db_session: Session):
    _criar_role(db_session, name="List_Role_1")
    _criar_role(db_session, name="List_Role_2")

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
    result = RolesService.get_roles(qp, db_session)

    assert result is not None
    if isinstance(result, dict):
        assert "data" in result or "items" in result
    else:
        assert hasattr(result, "data") or hasattr(result, "items")
