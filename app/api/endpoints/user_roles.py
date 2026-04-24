from fastapi import APIRouter, Response, Security, status
from pydantic.types import UUID4

from app import auth, schema
from app.db.session import _db
from app.services.user_roles_service import UserRolesService
from app.util import QueryParametersDep

router = APIRouter(prefix="/user-roles", tags=["UserRoles"])


@router.get(
    "/",
    response_model=schema.ResponseUserRoles,
    status_code=status.HTTP_200_OK,
)
def get_user_roles(
    query_parameters: QueryParametersDep,
    session: _db,
    Authentication: dict = Security(auth.get_current_payload, scopes=["admin"]),
) -> schema.ResponseUserRoles:
    """Realiza requisiçoes tipo **GET** em **UserRoles** models"""
    return UserRolesService.get_user_roles(query_parameters, session)


@router.post(
    "/",
    response_model=schema.GetUserRoles,
    status_code=status.HTTP_201_CREATED,
)
def create_user_roles(
    json_data: schema.PostUserRoles,
    session: _db,
    Authentication: dict = Security(auth.get_current_payload, scopes=["admin"]),
) -> schema.GetUserRoles:
    """Recebe uma requisição tipo `POST` contendo dados referente a **UserRoles**"""
    return UserRolesService.create_user_role(json_data, session)


@router.patch(
    "/{id}",
    response_model=schema.GetUserRoles,
    status_code=status.HTTP_200_OK,
)
def update_user_roles_by_uuid(
    id: UUID4,
    json_data: schema.PatchUserRoles,
    session: _db,
    Authentication: dict = Security(auth.get_current_payload, scopes=["admin"]),
) -> schema.GetUserRoles:
    """Atualiza um dado na tabela **UserRoles** a partir de um UUID valido"""
    return UserRolesService.patch_user_role(id, json_data, session)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_roles_by_uuid(
    id: UUID4,
    session: _db,
    Authentication: dict = Security(auth.get_current_payload, scopes=["admin"]),
):
    """Deleta um dado na tabela **UserRoles** a partir do seu UUID"""
    UserRolesService.delete_user_role(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
