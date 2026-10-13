import logging
from uuid import UUID

from sqlalchemy import select

from app import error, models
from app.db import QueryBuilder, ServiceResponse, _db
from app.models import UserRoles
from app.schema import PatchUserRoles, PostUserRoles
from app.util import QueryParametersDep

logger = logging.getLogger(__name__)


class UserRolesService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo UserRoles.
    """

    @staticmethod
    async def get_user_roles(query_params: QueryParametersDep, session: _db):
        """Busca, filtra e pagina os registros de UserRoles.

        Delega a chamada para o método query_params do modelo UserRoles,
        passando os parâmetros de consulta específicos.

        Args:
            query_params (QueryParametersDep): Objeto encapsulado com os
                parâmetros de consulta.
            session (_db): Sessão com o banco de dados.

        Returns:
            dict: Um dicionário contendo a lista de 'items' (UserRoles) e
                  o 'total' de registros encontrados.
        """

        logger.debug("Buscando associações entre usuários e papéis")
        builder = (
            QueryBuilder(models.UserRoles)
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
        logger.debug(
            "Associações entre usuários e papéis buscadas com sucesso"
        )
        return ServiceResponse(data=data, meta={"total_items": total_items})

    @staticmethod
    async def create_user_role(schema: PostUserRoles, session: _db):
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
        logger.debug("Iniciando criação de associação entre usuário e papel")

        stmt = select(
            select(models.Users.id)
            .where(
                models.Users.id == schema.user_id,
                models.Users.is_deleted.is_(False),
            )
            .exists()
        )
        if not await session.scalar(stmt):
            errors.append(
                {
                    "loc": ["body", "user_id"],
                    "msg": "UUID do usuario não encontrado.",
                    "type": "value_error",
                }
            )

        if not await session.get(models.Roles, schema.role_id):
            errors.append(
                {
                    "loc": ["body", "role_id"],
                    "msg": "UUID do papel não encontrado.",
                    "type": "value_error",
                }
            )

        if errors:
            logger.warning(
                "Erros encontrados ao validar associação entre usuário e papel"
            )
            raise error.ValidationException(errors)

        data = UserRoles(**schema.model_dump())
        session.add(data)
        await session.commit()
        await session.refresh(data)
        logger.info("Associação entre usuário e papel criada com sucesso")
        return data

    @staticmethod
    async def patch_user_role(id: UUID, schema: PatchUserRoles, session: _db):
        """Atualiza parcialmente uma associação UserRoles existente.

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
            UserRoles: O objeto UserRoles atualizado.
        """
        logger.debug(
            "Iniciando atualização de associação entre usuário e papel"
        )
        item_to_update = await session.get(UserRoles, id)

        if not item_to_update:
            logger.warning("Associação entre usuário e papel não encontrada")
            raise error.CustomException(404, "ID não encontrado")

        update_data = schema.model_dump(exclude_unset=True, exclude_none=True)
        errors = []

        stmt = select(
            select(models.Users.id)
            .where(
                models.Users.id == update_data["user_id"],
                models.Users.is_deleted.is_(False),
            )
            .exists()
        )
        if "user_id" in update_data and not await session.scalar(stmt):
            errors.append(
                {
                    "loc": ["body", "user_id"],
                    "msg": "UUID do usuario não encontrado.",
                    "type": "value_error",
                }
            )

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

        if errors:
            logger.warning(
                "Erros encontrados ao validar associação entre usuário e papel"
            )
            raise error.ValidationException(errors)

        for key, value in update_data.items():
            setattr(item_to_update, key, value)

        session.add(item_to_update)
        await session.commit()
        await session.refresh(item_to_update)

        logger.info("Associação entre usuário e papel atualizada com sucesso")
        return item_to_update

    @staticmethod
    async def delete_user_role(id: UUID, session: _db):
        """Deleta uma associação UserRoles existente do banco de dados.

        Args:
            id (UUID): O ID (UUID) da associação a ser deletada.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a associação com o ID
                           fornecido não for encontrada.

        Returns:
            UserRoles: O objeto UserRoles que foi deletado.
        """
        logger.debug("Iniciando exclusão de associação entre usuário e papel")
        item_to_delete = await session.get(UserRoles, id)

        if not item_to_delete:
            logger.warning("Associação entre usuário e papel não encontrada")
            raise error.CustomException(404, "ID não encontrado")

        await session.delete(item_to_delete)
        await session.commit()

        logger.info("Associação entre usuário e papel excluída com sucesso")
        return item_to_delete
