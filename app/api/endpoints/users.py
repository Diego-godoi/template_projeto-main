# app/routers/users.py

from fastapi import APIRouter, Response, Security, status
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
        auth.get_current_payload, scopes=["user", "admin"]
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
    json_data: schema.PostUsers,
    session: _db,  # <-- Dependência da sessão adicionada
) -> schema.GetUsers:
    """Recebe uma requisição tipo `POST` contendo dados referente a **Users**"""
    return await UsersService.create_user(json_data, session)


@router.patch(
    "/{id}",
    response_model=schema.GetUsers,
    status_code=status.HTTP_200_OK,
)
async def update_users_by_uuid(
    id: UUID4,
    json_data: schema.PatchUsers,
    session: _db,
    Authentication: dict = Security(auth.get_current_payload, scopes=["user"]),
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
    Authentication: dict = Security(auth.get_current_payload, scopes=["user"]),
):
    """Deleta um dado na tabela **Users** a partir do seu UUID"""
    await UsersService.delete_user(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
