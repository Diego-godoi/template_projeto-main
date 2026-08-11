from fastapi import APIRouter, Response, Security, status
from pydantic.types import UUID4

from app import auth, schema
from app.db.session import _db
from app.services.permissions_service import PermissionsService
from app.util import QueryParametersDep

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get(
    "/",
    response_model=schema.ResponsePermissions,
    status_code=status.HTTP_200_OK,
)
async def get_permissions(
    query_parameters: QueryParametersDep,
    session: _db,
    Authorization: dict = Security(
        auth.get_current_payload, scopes=["read:permissions"]
    ),
) -> schema.ResponsePermissions:
    """Realiza requisiçoes tipo **GET** em **Permissions** models

    Args:
        query_parameters (object): Parâmetros de consulta 'QueryParametersDep'.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        Retorna os dados da consulta em lista do schema `GetPermissions`.
    """
    return await PermissionsService.get_permissions(query_parameters, session)


@router.post(
    "/",
    response_model=schema.GetPermissions,
    status_code=status.HTTP_201_CREATED,
)
async def create_permissions(
    json_data: schema.PostPermissions,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["write:permissions"]
    ),
) -> schema.GetPermissions:
    """Recebe uma requisição tipo `POST` contendo dados referente a **Permissions**

    Args:
        json_data (schema.PostPermissions): schema de dados para serem criados **Permissions**
        Authentication (str, optional): **OAuth 2.0**. Defaults to None.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        GetPermissions: Retorna o dado com as informaçoes de criaçao atualizadas.
    """
    return await PermissionsService.create_permission(json_data, session)


@router.patch(
    "/{id}",
    response_model=schema.GetPermissions,
    status_code=status.HTTP_200_OK,
)
async def update_permissions_by_id(
    id: UUID4,
    json_data: schema.PatchPermissions,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["update:permissions"]
    ),
) -> schema.GetPermissions:
    """Atualiza um dado na tabela **Permissions** a partir de um UUID valido

    Args:
        id (UUID4): UUID do dado a ser atualizado
        json_data (schema.PatchPermissions): Schema de dados que pode ser atualizados.
        Authentication (str, optional): **OAuth 2.0**. Defaults to None.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        schema.GetPermissions: Retorna os dado com as informaçoes atualizadas.
    """
    return await PermissionsService.patch_permission(id, json_data, session)


@router.delete("/{id}")
async def delete_permissions_by_id(
    id: UUID4,
    session: _db,
    Authentication: dict = Security(
        auth.get_current_payload, scopes=["delete:permissions"]
    ),
):
    """Deleta um dado na tabela **Permissions** a partir do seu UUID

    Args:
        id (UUID4): UUID do dado a ser deletado
        Authentication (str, optional): **OAuth 2.0**. Defaults to None.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        None: "No content"
    """
    await PermissionsService.delete_permission(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
