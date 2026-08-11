from uuid import UUID

from sqlalchemy import select

from app import error, models
from app.db import QueryBuilder, ServiceResponse, _db
from app.models import Permissions
from app.schema import PatchPermissions, PostPermissions
from app.util import QueryParametersDep


class PermissionsService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo Permissions.
    """

    @staticmethod
    async def get_permissions(query_params: QueryParametersDep, session: _db):
        """Busca, filtra e pagina os registros de Permissions.

        Utiliza os parâmetros de consulta fornecidos para filtrar
        e formatar a resposta da listagem.

        Args:
            query_params (QueryParametersDep): Objeto encapsulado com os
                parâmetros de consulta.
            session (_db): Sessão com o banco de dados.

        Returns:
            dict: Um dicionário contendo a lista de 'items' (Permissions) e
                  o 'total' de registros encontrados.
        """
        builder = (
            QueryBuilder(models.Permissions)
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
    async def create_permission(schema: PostPermissions, session: _db):
        """Cria uma nova permissão no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            schema (PostPermissions): Dados de entrada validados para a criação da permissão.
            session (_db): Sessão da transação com o banco de dados.

        Returns:
            Permissions: O objeto Permissions recém-criado e salvo no banco.
        """
        errors = []

        stmt = (
            select(Permissions).where(Permissions.name == schema.name).limit(1)
        )
        existing_role = (await session.execute(stmt)).scalars().first()
        if existing_role:
            errors.append(
                {
                    "loc": ["body", "name"],
                    "msg": f"'{schema.name}' já está cadastrado.",
                    "type": "value_error",
                }
            )

        if errors:
            raise error.ValidationException(errors)

        data = Permissions(**schema.model_dump())
        session.add(data)
        await session.commit()
        await session.refresh(data)
        return data

    @staticmethod
    async def patch_permission(
        id: UUID, schema: PatchPermissions, session: _db
    ):
        """Atualiza parcialmente uma permissão existente no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            id (UUID): O ID (UUID) da permissão a ser atualizada.
            schema (PatchPermissions): Dados de entrada com os campos a serem atualizados.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a permissão com o ID
                           fornecido não for encontrada.

        Returns:
            Permissions: O objeto Permissions atualizado.
        """
        permission_to_update = await session.get(Permissions, id)

        if not permission_to_update:
            raise error.CustomException(404, "ID não encontrado")

        update_data = schema.model_dump(exclude_unset=True, exclude_none=True)
        errors = []

        if "name" in update_data:
            stmt = (
                select(Permissions)
                .where(Permissions.name == update_data["name"])
                .limit(1)
            )
            existing_permission = (
                (await session.execute(stmt)).scalars().first()
            )
            if existing_permission and existing_permission.id != id:
                errors.append(
                    {
                        "loc": ["body", "name"],
                        "msg": f"'{update_data['name']}' já está cadastrado.",
                        "type": "value_error",
                    }
                )

        if errors:
            raise error.ValidationException(errors)

        for key, value in update_data.items():
            setattr(permission_to_update, key, value)

        session.add(permission_to_update)
        await session.commit()
        await session.refresh(permission_to_update)

        return permission_to_update

    @staticmethod
    async def delete_permission(id: UUID, session: _db):
        """Deleta uma permissão existente do banco de dados.

        Args:
            id (UUID): O ID (UUID) da permissão a ser deletada.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a permissão com o ID
                           fornecido não for encontrada.

        Returns:
            Permissions: O objeto Permissions que foi deletado (em estado 'detached').
        """
        permission_to_delete = await session.get(Permissions, id)

        if not permission_to_delete:
            raise error.CustomException(404, "ID não encontrado")

        await session.delete(permission_to_delete)
        await session.commit()

        return permission_to_delete
