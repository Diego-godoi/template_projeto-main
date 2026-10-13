# app/routers/users.py

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request,
    Response,
    status,
)
from pydantic.types import UUID4

from app import auth, schema
from app.core.limiter import HEAVY_LIMIT, PUBLIC_LIMIT, limiter
from app.db.session import _db
from app.services.users_service import UsersService
from app.util import QueryParametersDep

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=schema.ResponseUsers,
    status_code=status.HTTP_200_OK,
)
async def get_users(
    request: Request,
    query_parameters: QueryParametersDep,
    session: _db,
    Authentication: dict = Depends(auth.require_roles("Manager", "Admin")),
) -> schema.ResponseUsers:
    """Realiza requisiçoes tipo **GET** em **Users** models"""
    return await UsersService.get_users(query_parameters, session)


@router.post(
    "/",
    response_model=schema.GetUsers,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(PUBLIC_LIMIT)
async def create_users(
    request: Request,
    session: _db,
    json_data: Annotated[schema.PostUsers, Form()],
) -> schema.GetUsers:
    """Recebe uma requisição tipo `POST` (multipart/form-data) contendo dados e imagem de **Users**"""
    return await UsersService.create_user(json_data, session)


@router.patch(
    "/{id}",
    response_model=schema.GetUsers,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(HEAVY_LIMIT)
async def update_users_by_uuid(
    id: UUID4,
    request: Request,
    session: _db,
    json_data: Annotated[schema.PatchUsers, Form()],
    Authentication: dict = Depends(auth.require_roles("Admin")),
) -> schema.GetUsers:
    """Atualiza um dado na tabela **Users** a partir de um UUID valido"""
    return await UsersService.patch_user(id, json_data, session)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit(HEAVY_LIMIT)
async def delete_users_by_uuid(
    id: UUID4,
    request: Request,
    session: _db,
    Authentication: dict = Depends(auth.require_roles("Admin")),
):
    """Soft delete de um dado na tabela **Users** a partir do seu UUID"""
    await UsersService.delete_user(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
