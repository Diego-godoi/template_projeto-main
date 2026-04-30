from uuid import UUID

from sqlalchemy import func, select

from app import error, models
from app.db import QueryBuilder, ServiceResponse, _db
from app.models import Roles
from app.schema import PatchRoles, PostRoles
from app.util import QueryParametersDep


class RolesService:
    """
    Camada de serviço para agrupar operações de CRUD para o modelo Roles.
    """

    @staticmethod
    async def get_roles(query_params: QueryParametersDep, session: _db):
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

        meta = {
            "total_items": (
                await session.execute(select(func.count(models.Roles.id)))
            ).scalar()
        }
        stmt = (
            QueryBuilder(models.Roles)
            .filter(
                query_params.attribute,
                query_params.value,
                query_params.operator,
            )
            .filter_json(query_params.json_string, query_params.operator)
            .include_only(query_params.include)
            .paginate(query_params.skip, query_params.limit)
            .build()
        )
        data = (await session.execute(stmt)).scalars().unique().all()
        return ServiceResponse(data=data, meta=meta)

    @staticmethod
    async def create_role(schema: PostRoles, session: _db):
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

        stmt = select(Roles).where(Roles.name == schema.name).limit(1)
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

        data = Roles(**schema.model_dump())
        session.add(data)
        await session.commit()
        await session.refresh(data)
        return data

    @staticmethod
    async def patch_role(id: UUID, schema: PatchRoles, session: _db):
        """Atualiza parcialmente uma role existente no banco de dados.

        Valida todas as regras de negócio e acumula os erros antes de
        lançar uma única exceção com a lista completa.

        Args:
            id (UUID): O ID (UUID) da role a ser atualizada.
            schema (PatchRoles): Dados de entrada com os campos a serem atualizados.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a role com o ID
                           fornecido não for encontrada.

        Returns:
            Roles: O objeto Roles atualizado.
        """
        role_to_update = await session.get(Roles, id)

        if not role_to_update:
            raise error.CustomException(404, "ID não encontrado")

        update_data = schema.model_dump(exclude_unset=True)
        errors = []

        if "name" in update_data:
            stmt = (
                select(Roles).where(Roles.name == update_data["name"]).limit(1)
            )
            existing_role = (await session.execute(stmt)).scalars().first()
            if existing_role and existing_role.id != id:
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
            setattr(role_to_update, key, value)

        session.add(role_to_update)
        await session.commit()
        await session.refresh(role_to_update)

        return role_to_update

    @staticmethod
    async def delete_role(id: UUID, session: _db):
        """Deleta uma role existente do banco de dados.

        Args:
            id (UUID): O ID (UUID) da role a ser deletada.
            session (_db): Sessão da transação com o banco de dados.

        Raises:
            CustomException: Lançada com status 404 se a role com o ID
                           fornecido não for encontrada.

        Returns:
            Roles: O objeto Roles que foi deletado (em estado 'detached').
        """
        role_to_delete = await session.get(Roles, id)

        if not role_to_delete:
            raise error.CustomException(404, "ID não encontrado")

        await session.delete(role_to_delete)
        await session.commit()

        return role_to_delete
