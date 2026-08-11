from fastapi import APIRouter, Response, Security, status
from pydantic.types import UUID4

from app import auth, schema
from app.db.session import _db
from app.services.role_permissions_service import RolePermissionsService
from app.util import QueryParametersDep

router = APIRouter(prefix="/role-permissions", tags=["role-permissions"])


@router.get(
    "/",
    response_model=schema.ResponseRolePermissions,
    status_code=status.HTTP_200_OK,
)
async def get_role_permissions(
    query_parameters: QueryParametersDep,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["read:role-permissions"]
    ),
) -> schema.ResponseRolePermissions:
    """Realiza requisiçoes tipo **GET** em **RolePermissions** models"""
    return await RolePermissionsService.get_role_permissions(
        query_parameters, session
    )


@router.post(
    "/",
    response_model=schema.GetRolePermissions,
    status_code=status.HTTP_201_CREATED,
)
async def create_role_permission(
    json_data: schema.PostRolePermissions,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["write:role-permissions"]
    ),
) -> schema.GetRolePermissions:
    """Recebe uma requisição tipo `POST` contendo dados referente a **RolePermissions**"""
    return await RolePermissionsService.create_role_permission(
        json_data, session
    )


@router.patch(
    "/{id}",
    response_model=schema.GetRolePermissions,
    status_code=status.HTTP_200_OK,
)
async def update_role_permission_by_uuid(
    id: UUID4,
    json_data: schema.PatchRolePermissions,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["update:role-permissions"]
    ),
) -> schema.GetRolePermissions:
    """Atualiza um dado na tabela **RolePermissions** a partir de um UUID valido"""
    return await RolePermissionsService.patch_role_permission(
        id, json_data, session
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role_permission_by_uuid(
    id: UUID4,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["delete:role-permissions"]
    ),
):
    """Deleta um dado na tabela **RolePermissions** a partir do seu UUID"""
    await RolePermissionsService.delete_role_permission(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
