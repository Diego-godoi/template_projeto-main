from uuid import UUID

from app import error, models
from app.db import QueryBuilder, ServiceResponse, _db
from app.models import RolePermissions
from app.schema import PatchRolePermissions, PostRolePermissions
from app.util import QueryParametersDep


class RolePermissionsService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo RolePermissions.
    """

    @staticmethod
    async def get_role_permissions(
        query_params: QueryParametersDep, session: _db
    ):
        """Busca, filtra e pagina os registros de RolePermissions.

        Delega a chamada para o método query_params do modelo RolePermissions,
        passando os parâmetros de consulta específicos.

        Args:
            query_params (QueryParametersDep): Objeto encapsulado com os
                parâmetros de consulta.
            session (_db): Sessão com o banco de dados.

        Returns:
            dict: Um dicionário contendo a lista de 'items' (RolePermissions) e
                  o 'total' de registros encontrados.
        """
        builder = (
            QueryBuilder(models.RolePermissions)
            .filter(
                query_params.attribute,
                query_params.value,
                query_params.operator,
            )
            .filter_json(query_params.json_string, query_params.operator)
            .include_only(query_params.include)
        )
        total_items = (await session.execute(builder.build_count())).scalar()
        stmt = builder.paginate(query_params.skip, query_params.limit).build()
        data = (await session.execute(stmt)).scalars().unique().all()
        meta = {"total_items": total_items}
        return ServiceResponse(data=data, meta=meta)

    @staticmethod
    async def create_role_permission(
        schema: PostRolePermissions, session: _db
    ):
        """Associa um User a uma Role no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            schema (PostUserRoles): Dados de entrada (user_id, role_id).
            session (_db): Sessão da transação com o banco de dados.

        Returns:
            UserRoles: O objeto de associação UserRoles recém-criado.
        """
        errors = []

        if not await session.get(models.Roles, schema.role_id):
            errors.append(
                {
                    "loc": ["body", "role_id"],
                    "msg": "UUID do papel não encontrado.",
                    "type": "value_error",
                }
            )

        if not await session.get(models.Permissions, schema.permission_id):
            errors.append(
                {
                    "loc": ["body", "permission_id"],
                    "msg": "UUID da permissão não encontrada.",
                    "type": "value_error",
                }
            )

        if errors:
            raise error.ValidationException(errors)

        data = RolePermissions(**schema.model_dump())
        session.add(data)
        await session.commit()
        await session.refresh(data)
        return data

    @staticmethod
    async def patch_role_permission(
        id: UUID, schema: PatchRolePermissions, session: _db
    ):
        """Atualiza parcialmente uma associação RolePermissions existente.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            id (UUID): O ID (UUID) da associação a ser atualizada.
            schema (PatchUserRoles): Dados de entrada com os campos a serem atualizados.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a associação com o ID
                           fornecido não for encontrada.

        Returns:
            RolePermissions: O objeto RolePermissions atualizado.
        """
        item_to_update = await session.get(RolePermissions, id)

        if not item_to_update:
            raise error.CustomException(404, "ID não encontrado")

        update_data = schema.model_dump(exclude_unset=True, exclude_none=True)
        errors = []

        if "role_id" in update_data and not await session.get(
            models.Roles, update_data["role_id"]
        ):
            errors.append(
                {
                    "loc": ["body", "role_id"],
                    "msg": "UUID do papel não encontrado.",
                    "type": "value_error",
                }
            )

        if "role_id" in update_data and not await session.get(
            models.Permissions, update_data["permission_id"]
        ):
            errors.append(
                {
                    "loc": ["body", "permission_id"],
                    "msg": "UUID da permissão não encontrada.",
                    "type": "value_error",
                }
            )

        if errors:
            raise error.ValidationException(errors)

        for key, value in update_data.items():
            setattr(item_to_update, key, value)

        session.add(item_to_update)
        await session.commit()
        await session.refresh(item_to_update)

        return item_to_update

    @staticmethod
    async def delete_role_permission(id: UUID, session: _db):
        """Deleta uma associação RolePermissions existente do banco de dados.

        Args:
            id (UUID): O ID (UUID) da associação a ser deletada.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a associação com o ID
                           fornecido não for encontrada.

        Returns:
            RolePermissions: O objeto RolePermissions que foi deletado.
        """
        item_to_delete = await session.get(RolePermissions, id)

        if not item_to_delete:
            raise error.CustomException(404, "ID não encontrado")

        await session.delete(item_to_delete)
        await session.commit()

        return item_to_delete
