from uuid import UUID

from fastapi import HTTPException

from app.db import _db
from app.error import ValidationException
from app.models import Roles
from app.schema import PatchRoles, PostRoles
from app.util import QueryParametersDep


class RolesService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo Roles.
    """

    @staticmethod
    def get_roles(query_params: QueryParametersDep, session: _db):
        """Busca, filtra e pagina os registros de Roles.

        Utiliza os parâmetros de consulta fornecidos para filtrar
        e formatar a resposta da listagem.

        Args:
            query_params (QueryParametersDep): Objeto encapsulado com os
                parâmetros de consulta.
            session (_db): Sessão com o banco de dados.

        Returns:
            dict: Um dicionário contendo a lista de 'items' (Roles) e
                  o 'total' de registros encontrados.
        """

        query_args = vars(query_params)

        return Roles.query_params(_db=session, **query_args)

    @staticmethod
    def create_role(schema: PostRoles, session: _db):
        """Cria uma nova role no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            schema (PostRoles): Dados de entrada validados para a criação da role.
            session (_db): Sessão da transação com o banco de dados.

        Returns:
            Roles: O objeto Roles recém-criado e salvo no banco.
        """
        errors = []

        if Roles.get(_db=session, attribute="name", value=schema.name):
            errors.append(
                {
                    "loc": ["body", "name"],
                    "msg": f"'{schema.name}' já está cadastrado.",
                    "type": "value_error",
                }
            )

        if errors:
            raise ValidationException(errors)

        data = Roles(**schema.model_dump())
        session.add(data)
        session.commit()
        session.refresh(data)
        return data

    @staticmethod
    def patch_role(id: UUID, schema: PatchRoles, session: _db):
        """Atualiza parcialmente uma role existente no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            id (UUID): O ID (UUID) da role a ser atualizada.
            schema (PatchRoles): Dados de entrada com os campos a serem atualizados.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            HTTPException: Lançada com status 404 se a role com o ID
                           fornecido não for encontrada.

        Returns:
            Roles: O objeto Roles atualizado.
        """
        role_to_update = session.get(Roles, id)

        if not role_to_update:
            raise HTTPException(status_code=404, detail="ID não encontrado")

        update_data = schema.model_dump(exclude_unset=True)
        errors = []

        if "name" in update_data:
            existing_role = Roles.get(
                _db=session, attribute="name", value=update_data["name"]
            )
            if existing_role and existing_role.id != id:
                errors.append(
                    {
                        "loc": ["body", "name"],
                        "msg": f"'{update_data['name']}' já está cadastrado.",
                        "type": "value_error",
                    }
                )

        if errors:
            raise ValidationException(errors)

        for key, value in update_data.items():
            setattr(role_to_update, key, value)

        session.add(role_to_update)
        session.commit()
        session.refresh(role_to_update)

        return role_to_update

    @staticmethod
    def delete_role(id: UUID, session: _db):
        """Deleta uma role existente do banco de dados.

        Args:
            id (UUID): O ID (UUID) da role a ser deletada.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            HTTPException: Lançada com status 404 se a role com o ID
                           fornecido não for encontrada.

        Returns:
            Roles: O objeto Roles que foi deletado (em estado 'detached').
        """
        role_to_delete = session.get(Roles, id)

        if not role_to_delete:
            raise HTTPException(status_code=404, detail="ID não encontrado")

        session.delete(role_to_delete)
        session.commit()
