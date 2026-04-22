# app/routers/users.py

from fastapi import APIRouter, Response, status
from fastapi.param_functions import Depends
from pydantic.types import UUID4

from app import auth, error, schema
from app.db.session import _db
from app.services.users_service import UsersService
from app.util import QueryParametersDep

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=schema.ResponseUsers,
    status_code=status.HTTP_200_OK,
)
def get_users(
    query_parameters: QueryParametersDep,
    session: _db,
    Authentication: str = Depends(auth.Key.n1),
) -> schema.ResponseUsers:
    """Realiza requisiçoes tipo **GET** em **Users** models"""
    try:
        return UsersService.get_users(query_parameters, session)
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.post(
    "/",
    response_model=schema.GetUsers,
    status_code=status.HTTP_201_CREATED,
)
def create_users(
    json_data: schema.PostUsers,
    session: _db,  # <-- Dependência da sessão adicionada
    Authentication: str = Depends(auth.Key.n0),
) -> schema.GetUsers:
    """Recebe uma requisição tipo `POST` contendo dados referente a **Users**"""
    try:
        return UsersService.create_user(json_data, session)
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.patch(
    "/{id}",
    response_model=schema.GetUsers,
    status_code=status.HTTP_200_OK,
)
def update_users_by_uuid(
    id: UUID4,
    json_data: schema.PatchUsers,
    session: _db,
    Authentication: str = Depends(auth.Key.n1),
) -> schema.GetUsers:
    """Atualiza um dado na tabela **Users** a partir de um UUID valido"""
    try:
        # Lógica agora chama o serviço
        return UsersService.patch_user(id, json_data, session)
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_users_by_uuid(
    id: UUID4,
    session: _db,
    Authentication: str = Depends(auth.Key.n1),
):
    """Deleta um dado na tabela **Users** a partir do seu UUID"""
    try:
        UsersService.delete_user(id, session)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise error.custom_HTTPException(e)
