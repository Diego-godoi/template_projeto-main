from uuid import UUID

from app import models, error
from app.db import _db
from app.models import UserRoles
from app.schema import PatchUserRoles, PostUserRoles
from app.util import QueryParametersDep


class UserRolesService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo UserRoles.
    """

    @staticmethod
    def get_user_roles(query_params: QueryParametersDep, session: _db):
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

        query_args = vars(query_params)
        return UserRoles.query_params(_db=session, **query_args)

    @staticmethod
    def create_user_role(schema: PostUserRoles, session: _db):
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

        if not session.get(models.Users, schema.user_id):
            errors.append(
                {
                    "loc": ["body", "user_id"],
                    "msg": "UUID do usuario não encontrado.",
                    "type": "value_error",
                }
            )

        if not session.get(models.Roles, schema.role_id):
            errors.append(
                {
                    "loc": ["body", "role_id"],
                    "msg": "UUID do papel não encontrado.",
                    "type": "value_error",
                }
            )

        if errors:
            raise error.ValidationException(errors)

        data = UserRoles(**schema.model_dump())
        session.add(data)
        session.commit()
        session.refresh(data)
        return data

    @staticmethod
    def patch_user_role(id: UUID, schema: PatchUserRoles, session: _db):
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
        item_to_update = session.get(UserRoles, id)

        if not item_to_update:
            raise error.CustomException(404, "ID não encontrado")

        update_data = schema.model_dump(exclude_unset=True)
        errors = []

        if "user_id" in update_data and not session.get(
            models.Users, update_data["user_id"]
        ):
            errors.append(
                {
                    "loc": ["body", "user_id"],
                    "msg": "UUID do usuario não encontrado.",
                    "type": "value_error",
                }
            )

        if "role_id" in update_data and not session.get(
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
            raise error.ValidationException(errors)

        for key, value in update_data.items():
            setattr(item_to_update, key, value)

        session.add(item_to_update)
        session.commit()
        session.refresh(item_to_update)

        return item_to_update

    @staticmethod
    def delete_user_role(id: UUID, session: _db):
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
        item_to_delete = session.get(UserRoles, id)

        if not item_to_delete:
            raise error.CustomException(404, "ID não encontrado")

        session.delete(item_to_delete)
        session.commit()

        return item_to_delete
