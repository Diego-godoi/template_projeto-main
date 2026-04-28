# app/services/users_service.py

from uuid import UUID

from sqlalchemy import select

from app import core, error, models, schema
from app.db import _db
from app.util import QueryParametersDep


class UsersService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo Users.
    """

    @staticmethod
    async def get_users(query_params: QueryParametersDep, session: _db):
        """Busca, filtra e pagina os registros de Users.

        Delega a chamada para o método query_params do próprio modelo.

        Args:
            query_params (QueryParametersDep): Objeto encapsulado com os
                parâmetros de consulta.
            session (_db): Sessão com o banco de dados.

        Returns:
            dict: Um dicionário contendo a lista de 'items' (Users) e
                  o 'total' de registros encontrados.
        """
        query_args = vars(query_params)
        # Segue o padrão do RolesService, delegando ao modelo com Sessão
        return await models.Users.query_params(_db=session, **query_args)

    @staticmethod
    async def create_user(schema: schema.PostUsers, session: _db):
        """Cria um novo user no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            schema (PostUsers): Dados de entrada validados (incluindo senha).
            session (Session): Sessão da transação com o banco de dados.

        Returns:
            Users: O objeto Users recém-criado e salvo no banco.
        """
        errors = []
        stmt = (
            select(models.Users)
            .where(models.Users.email == schema.email)
            .limit(1)
        )
        if (await session.execute(stmt)).scalars().first():
            errors.append(
                {
                    "loc": ["body", "email"],
                    "msg": f"'{schema.email}' já está cadastrado.",
                    "type": "value_error",
                }
            )

        stmt = (
            select(models.Users).where(models.Users.cpf == schema.cpf).limit(1)
        )
        if (await session.execute(stmt)).scalars().first():
            errors.append(
                {
                    "loc": ["body", "cpf"],
                    "msg": f"'{schema.cpf}' já está cadastrado.",
                    "type": "value_error",
                }
            )

        if errors:
            raise error.ValidationException(errors)

        user_data = schema.model_dump()
        user_data["password"] = await core.get_password_hash(schema.password)
        data = models.Users(**user_data)
        session.add(data)
        await session.commit()
        await session.refresh(data)
        return data

    @staticmethod
    async def patch_user(id: UUID, schema: schema.PatchUsers, session: _db):
        """Atualiza parcialmente um user existente no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            id (UUID): O ID (UUID) do user a ser atualizado.
            schema (PatchUsers): Dados de entrada com os campos a serem atualizados.
            session (Session): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se o user com o ID
                           fornecido não for encontrado.

        Returns:
            Users: O objeto Users atualizado.
        """
        user_to_update = await session.get(models.Users, id)

        if not user_to_update:
            raise error.CustomException(404, "ID não encontrado")

        # Pega apenas os dados que foram enviados
        update_data = schema.model_dump(exclude_unset=True)
        errors = []

        if "email" in update_data:
            stmt = (
                select(models.Users)
                .where(models.Users.email == update_data["email"])
                .limit(1)
            )
            existing_user = (await session.execute(stmt)).scalars().first()
            if existing_user and existing_user.id != id:
                errors.append(
                    {
                        "loc": ["body", "email"],
                        "msg": f"'{update_data['email']}' já está cadastrado.",
                        "type": "value_error",
                    }
                )

        if "cpf" in update_data:
            stmt = (
                select(models.Users)
                .where(models.Users.cpf == update_data["cpf"])
                .limit(1)
            )
            existing_user = (await session.execute(stmt)).scalars().first()
            if existing_user and existing_user.id != id:
                errors.append(
                    {
                        "loc": ["body", "cpf"],
                        "msg": f"'{update_data['cpf']}' já está cadastrado.",
                        "type": "value_error",
                    }
                )

        if errors:
            raise error.ValidationException(errors)

        # Atualiza os campos no objeto (ativa setters como o de 'password')
        for key, value in update_data.items():
            if key == "password":
                value = await core.get_password_hash(value)
            setattr(user_to_update, key, value)

        session.add(user_to_update)
        await session.commit()
        await session.refresh(user_to_update)

        return user_to_update

    @staticmethod
    async def delete_user(id: UUID, session: _db):
        """Deleta um user existente do banco de dados.

        Args:
            id (UUID): O ID (UUID) do user a ser deletado.
            session (Session): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se o user com o ID
                           fornecido não for encontrado.

        Returns:
            Users: O objeto Users que foi deletado (em estado 'detached').
        """
        user_to_delete = await session.get(models.Users, id)

        if not user_to_delete:
            raise error.CustomException(404, "ID não encontrado")

        await session.delete(user_to_delete)
        await session.commit()

        return user_to_delete
