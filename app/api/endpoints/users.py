# app/routers/users.py


from fastapi import (
    APIRouter,
    Depends,
    Response,
    Security,
    status,
)
from pydantic.types import UUID4

from app import auth, schema
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
    query_parameters: QueryParametersDep,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["read:users"]
    ),
) -> schema.ResponseUsers:
    """Realiza requisiçoes tipo **GET** em **Users** models"""
    return await UsersService.get_users(query_parameters, session)


@router.post(
    "/",
    response_model=schema.GetUsers,
    status_code=status.HTTP_201_CREATED,
)
async def create_users(
    session: _db,
    json_data: schema.PostUsers = Depends(schema.PostUsers.as_form),
) -> schema.GetUsers:
    """Recebe uma requisição tipo `POST` (multipart/form-data) contendo dados e imagem de **Users**"""
    return await UsersService.create_user(json_data, session)


@router.patch(
    "/{id}",
    response_model=schema.GetUsers,
    status_code=status.HTTP_200_OK,
)
async def update_users_by_uuid(
    id: UUID4,
    session: _db,
    json_data=Depends(schema.PatchUsers.as_form),
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["update:users"]
    ),
) -> schema.GetUsers:
    """Atualiza um dado na tabela **Users** a partir de um UUID valido"""
    return await UsersService.patch_user(id, json_data, session)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_users_by_uuid(
    id: UUID4,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["delete:users"]
    ),
):
    """Soft delete de um dado na tabela **Users** a partir do seu UUID"""
    await UsersService.delete_user(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
