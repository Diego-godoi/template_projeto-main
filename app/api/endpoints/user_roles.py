from fastapi import APIRouter, Depends, Request, Response, status
from pydantic.types import UUID4

from app import auth, schema
from app.core.limiter import HEAVY_LIMIT, limiter
from app.db.session import _db
from app.services.user_roles_service import UserRolesService
from app.util import QueryParametersDep

router = APIRouter(
    prefix="/user-roles",
    tags=["UserRoles"],
    dependencies=[Depends(auth.require_roles("Admin"))],
)


@router.get(
    "/",
    response_model=schema.ResponseUserRoles,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(HEAVY_LIMIT)
async def get_user_roles(
    request: Request,
    query_parameters: QueryParametersDep,
    session: _db,
) -> schema.ResponseUserRoles:
    """Realiza requisiçoes tipo **GET** em **UserRoles** models"""
    return await UserRolesService.get_user_roles(query_parameters, session)


@router.post(
    "/",
    response_model=schema.GetUserRoles,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(HEAVY_LIMIT)
async def create_user_roles(
    request: Request,
    json_data: schema.PostUserRoles,
    session: _db,
) -> schema.GetUserRoles:
    """Recebe uma requisição tipo `POST` contendo dados referente a **UserRoles**"""
    return await UserRolesService.create_user_role(json_data, session)


@router.patch(
    "/{id}",
    response_model=schema.GetUserRoles,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(HEAVY_LIMIT)
async def update_user_roles_by_uuid(
    id: UUID4,
    request: Request,
    json_data: schema.PatchUserRoles,
    session: _db,
) -> schema.GetUserRoles:
    """Atualiza um dado na tabela **UserRoles** a partir de um UUID valido"""
    return await UserRolesService.patch_user_role(id, json_data, session)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit(HEAVY_LIMIT)
async def delete_user_roles_by_uuid(
    id: UUID4,
    request: Request,
    session: _db,
):
    """Deleta um dado na tabela **UserRoles** a partir do seu UUID"""
    await UserRolesService.delete_user_role(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
