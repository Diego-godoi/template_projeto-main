from fastapi import APIRouter, Depends, Request, Response, status
from pydantic.types import UUID4

from app import auth, schema
from app.core.limiter import HEAVY_LIMIT, limiter
from app.db.session import _db
from app.services.roles_service import RolesService
from app.util import QueryParametersDep

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get(
    "/",
    response_model=schema.ResponseRoles,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(HEAVY_LIMIT)
async def get_roles(
    request: Request,
    query_parameters: QueryParametersDep,
    session: _db,
    Authorization: dict = Depends(auth.require_roles("Manager", "Admin")),
) -> schema.ResponseRoles:
    """Realiza requisiçoes tipo **GET** em **Roles** models

    Args:
        query_parameters (object): Parâmetros de consulta 'QueryParametersDep'.

    Raises:
        HTTPException: {"status_code": "code" , "msg": "message"}

    Returns:
        Retorna os dados da consulta em lista do schema `GetRoles`.
    """
    return await RolesService.get_roles(query_parameters, session)


@router.post(
    "/", response_model=schema.GetRoles, status_code=status.HTTP_201_CREATED
)
@limiter.limit(HEAVY_LIMIT)
async def create_roles(
    request: Request,
    json_data: schema.PostRoles,
    session: _db,
    Authentication: dict = Depends(auth.require_roles("Admin")),
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
    return await RolesService.create_role(json_data, session)


@router.patch(
    "/{id}", response_model=schema.GetRoles, status_code=status.HTTP_200_OK
)
@limiter.limit(HEAVY_LIMIT)
async def update_roles_by_id(
    id: UUID4,
    request: Request,
    json_data: schema.PatchRoles,
    session: _db,
    Authentication: dict = Depends(auth.require_roles("Admin")),
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
    return await RolesService.patch_role(id, json_data, session)


@router.delete("/{id}")
@limiter.limit(HEAVY_LIMIT)
async def delete_roles_by_id(
    id: UUID4,
    request: Request,
    session: _db,
    Authentication: dict = Depends(auth.require_roles("Admin")),
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
    await RolesService.delete_role(id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
