from fastapi import APIRouter, Response, status
from fastapi.param_functions import Depends
from pydantic.types import UUID4

from app import auth, error, schema
from app.db.session import _db
from app.services.roles_service import RolesService
from app.util import QueryParametersDep

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get(
    "/",
    response_model=schema.ResponseRoles,
    status_code=status.HTTP_200_OK,
)
def get_roles(
    query_parameters: QueryParametersDep,
    session: _db,
    Authorization: str = Depends(auth.Key.n5),
) -> schema.ResponseRoles:
    """Realiza requisiçoes tipo **GET** em **Roles** models

    Args:
        query_parameters (object): Parâmetros de consulta 'QueryParametersDep'.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        Retorna os dados da consulta em lista do schema `GetRoles`.
    """
    try:
        return RolesService.get_roles(query_parameters, session)
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.post(
    "/", response_model=schema.GetRoles, status_code=status.HTTP_201_CREATED
)
def create_roles(
    json_data: schema.PostRoles,
    session: _db,
    Authentication: str = Depends(auth.Key.n5),
) -> schema.GetRoles:
    """Recebe uma requisição tipo `POST` contendo dados referente a **Roles**

    Args:
        json_data (schema.PostRoles): schema de dados para serem criados **Roles**
        Authentication (str, optional): **OAuth 2.0**. Defaults to None.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        GetRoles: Retorna o dado com as informaçoes de criaçao atualizadas.
    """
    try:
        return RolesService.create_role(json_data, session)
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.patch(
    "/{id}", response_model=schema.GetRoles, status_code=status.HTTP_200_OK
)
def update_roles_by_id(
    id: UUID4,
    json_data: schema.PatchRoles,
    session: _db,
    Authentication: str = Depends(auth.Key.n5),
) -> schema.GetRoles:
    """Atualiza um dado na tabela **Roles** a partir de um UUID valido

    Args:
        id (UUID4): UUID do dado a ser atualizado
        json_data (schema.PatchRoles): Schema de dados que pode ser atualizados.
        Authentication (str, optional): **OAuth 2.0**. Defaults to None.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        schema.GetRoles: Retorna os dado com as informaçoes atualizadas.
    """
    try:
        return RolesService.patch_role(id, json_data, session)
    except Exception as e:
        raise error.custom_HTTPException(e)


@router.delete("/{id}")
def delete_roles_by_id(
    id: UUID4,
    session: _db,
    Authentication: str = Depends(auth.Key.n5),
):
    """Deleta um dado na tabela **Roles** a partir do seu UUID

    Args:
        id (UUID4): UUID do dado a ser deletado
        Authentication (str, optional): **OAuth 2.0**. Defaults to None.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        None: "No content"
    """
    try:
        RolesService.delete_role(id, session)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise error.custom_HTTPException(e)
