import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import CHAR, Column, DateTime, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Session, load_only

from app import core
from app.error import CustomException, DatabaseException
from app.util.functions import pascal_to_snake_case

__all__ = ["Base"]


def generate_uuid():
    return uuid.uuid4()


class Response:
    def __init__(self, data: Any, meta: dict | None = None) -> None:
        self.data = data
        self.meta = meta if meta is not None else {}


class Base(DeclarativeBase):
    __name__: str
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )

    @declared_attr
    def __tablename__(cls) -> str:
        return pascal_to_snake_case(cls.__name__)

    async def create(self, _db: AsyncSession) -> object:
        try:
            data = self
            _db.add(data)
            await _db.flush()
            await _db.commit()
            await _db.refresh(data)
            return data

        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def login(
        self, attribute: str, value: Any, password: str, _db: AsyncSession
    ) -> object:
        """executa login em usuario

        Args:
            attribute (str): Nome do atributo para verificar o valor
            value (str): username para efetuar o login
            password (str): senha para ser verificada
            _db (AsyncSession): Sessão de banco de dados injetada

        Raises:
            CustomException: 404 usuario ou senha incorretos
            CustomException: 401 status do usuario inativo
            CustomException: 401 senha incorreta_

        Returns:
            object: _description_
        """
        try:
            stmt = select(self).where(getattr(self, attribute) == value)
            result = await _db.execute(stmt)
            data = result.scalars().first()

            if not data:
                raise CustomException(
                    status_code=404,
                    detail="Usuario ou senha invalidos",
                )
            if hasattr(data, "active"):
                if not data.active:
                    raise CustomException(
                        status_code=401, detail="Usuario Inativo"
                    )

            if not await core.verify_password(password, data.password):
                raise CustomException(
                    status_code=401,
                    detail="Usuario ou senha invalidos",
                )
            return data
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def query_by_partial_match(
        self, attribute: str, value: str, _db: AsyncSession
    ) -> object:
        """Realiza uma busca parcial nos registros de uma tabela baseada em um atributo e valor.

        Args:
            attribute (str): Nome do atributo a ser buscado.
            value (str): Valor parcial para busca. Deve ter entre 3 e 100 caracteres.
            _db (AsyncSession): Sessão providenciada pela injeção.

        Returns:
            object: Lista de objetos encontrados que correspondem à busca parcial.
        """
        try:
            if len(value) < 3:
                raise CustomException(
                    status_code=422,
                    detail="O termo de busca deve ter no mínimo 3 caracteres.",
                )
            if len(value) > 100:
                raise CustomException(
                    status_code=422,
                    detail="O termo de busca não pode exceder 100 caracteres.",
                )
            if hasattr(self, attribute):
                pattern = f"%{value}%"
                stmt = select(self).filter(
                    getattr(self, attribute).ilike(pattern)
                )
                result = await _db.execute(stmt)
                data = result.scalars().all()
                return data
            else:
                raise ValueError(
                    f"Atributo '{attribute}' não encontrado na tabela '{self.__tablename__}'."
                )
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def query_params(
        self,
        _db: AsyncSession,
        all_data: bool = False,
        attribute: str | None = None,
        value: str | None = None,
        json_string: dict | None = None,
        operator: str = "=",
        skip: int | None = None,
        limit: int | None = None,
        include: list[str] | None = None,
    ) -> object:
        """Este método realiza consultas personalizadas de acordo com a requisição do front-end.

        Args:
            _db (AsyncSession): Sessão repassada para query.
            all_data (bool): Se True, retorna uma lista de todos os dados equivalentes.
            attribute (str | None): Nome da chave a ser pesquisada. Deve ser um atributo válido da tabela.
            value (str | None): Conteúdo da busca relacionado à chave.
            operator (str): Operador de comparação. Padrão: "=".
            skip (int | None, optional): Número da página em caso de busca paginada.
            limit (int | None, optional): Quantidade por página.
            exclude (list[str] | None): Lista de atributos a serem excluídos da consulta.

        Raises:
            CustomException: 404 em caso de busca com um atributo não relacionado na tabela.
            CustomException: 422 em caso de uma consulta específica que não sejam passados atributos ou valores para busca.

        Returns:
            object: Retorna um objeto SQLAlchemy podendo ser vazio em caso de não encontrar nenhuma correspondência.
        """

        meta = {
            "total_items": (
                await _db.execute(select(func.count(self.id)))
            ).scalar()
        }

        try:
            query = select(self)
            if attribute:
                # Verificar se o atributo é válido
                if not hasattr(self, attribute):
                    raise CustomException(
                        status_code=404,
                        detail=f"Atributo '{attribute}' não encontrado na tabela '{self.__tablename__}'.",
                    )

                # Construir a condição de filtro com base no operador
                if operator == "=":
                    query = query.filter(getattr(self, attribute) == value)
                elif operator == "~":
                    if len(str(value)) < 3:
                        raise CustomException(
                            status_code=422,
                            detail="O termo de busca deve ter no mínimo 3 caracteres.",
                        )
                    if len(str(value)) > 100:
                        raise CustomException(
                            status_code=422,
                            detail="O termo de busca não pode exceder 100 caracteres.",
                        )
                    query = query.filter(
                        getattr(self, attribute).ilike(f"%{value}%")
                    )
                elif operator == "!":
                    query = query.filter(getattr(self, attribute) != value)
                elif operator == "<":
                    query = query.filter(getattr(self, attribute) < value)
                elif operator == ">":
                    query = query.filter(getattr(self, attribute) > value)
                elif operator == "<=":
                    query = query.filter(getattr(self, attribute) <= value)
                elif operator == ">=":
                    query = query.filter(getattr(self, attribute) >= value)
                elif operator == "|":
                    lower, upper = value.split("|")

                    # Tentar converter para diferentes tipos
                    types_to_try = [
                        int,
                        float,
                        lambda x: datetime.strptime(x, "%Y-%m-%d").date(),
                        lambda x: datetime.strptime(x, "%H:%M:%S").time(),
                    ]
                    for conversion_fn in types_to_try:
                        try:
                            lower_value = conversion_fn(lower)
                            upper_value = conversion_fn(upper)

                            # Lidar com intervalos de inteiros, floats, datas ou tempos
                            query = query.filter(
                                getattr(self, attribute).between(
                                    lower_value, upper_value
                                )
                            )
                            break  # Se a conversão for bem-sucedida, não precisamos continuar tentando outros tipos
                        except ValueError:
                            continue  # Se a conversão falhar, tentamos o próximo tipo

                    else:
                        # Se não conseguirmos converter para nenhum tipo, levantamos uma exceção informando o formato correto do intervalo
                        raise CustomException(
                            status_code=422,
                            detail="O intervalo deve estar em um formato compatível com inteiros, floats, datas ou tempos.",
                        )
                else:
                    raise CustomException(
                        status_code=422,
                        detail=f"Operador '{operator}' não suportado.",
                    )
            if json_string:
                # Verificar se há campos inválidos no json_string
                invalid_fields = [
                    field
                    for field in json_string.keys()
                    if not hasattr(self, field)
                ]
                if invalid_fields:
                    raise CustomException(
                        status_code=404,
                        detail=f"Os campos '{', '.join(invalid_fields)}' não encontrados na tabela '{self.__tablename__}'.",
                    )

                # Construir condições de filtro para cada par chave-valor do json_string
                for field, val in json_string.items():
                    if operator == "=":
                        query = query.filter(getattr(self, field) == val)
                    elif operator == "~":
                        attribute_type = (
                            getattr(self, field).property.columns[0].type
                        )
                        if not isinstance(
                            attribute_type, (String, Text, CHAR)
                        ):
                            raise CustomException(
                                422,
                                f"O operador ILIKE não pode ser aplicado ao tipo de dados do atributo '{field}'.",
                            )
                        query = query.filter(
                            getattr(self, field).ilike(f"%{val}%")
                        )
                    else:
                        raise CustomException(
                            status_code=422,
                            detail=f"Operador '{operator}' não suportado para json_string.",
                        )
            if include:
                include_columns = [
                    getattr(self, col) for col in include if hasattr(self, col)
                ]
                query = query.options(load_only(*include_columns))
            if skip is not None and limit is not None:
                _offset = skip * limit
                query = query.offset(_offset).limit(limit)
            data = (await _db.execute(query)).scalars().unique().all()

            return Response(data=data, meta=meta)

        except Exception as e:
            # CustomException (HTTP 4xx de negócio) borbulha, ValueError/SQLAlchemy viram DB Error
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def remove(self, id: UUID, _db: AsyncSession) -> str:
        """metodo utilizado para remover um dado da tabela correspondente

        Args:
            id (UUID): Id do dado a ser removido.
            _db (AsyncSession): Sessão DB.

        Raises:
            CustomException: 404 em caso de nao encontar dado correspondete ao id remetido.
            CustomException: 400 em caso de um problema durante a exclusão

        Returns:
            str: retorna ok em caso de sucesso.
        """
        try:
            stmt = select(self).filter_by(id=id)
            result = await _db.execute(stmt)
            data = result.scalars().first()
            if not data:
                raise CustomException(
                    status_code=404, detail="Dado não encontrado"
                )
            await _db.delete(data)
            await _db.commit()
            return "OK"
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def remove_data(self, id: UUID, _db: AsyncSession) -> list:
        """metodo utilizado para remover um dado da tabela correspondente
        Nota: Modificado para não interagir mais com manipulação de arquivos no SO. A camada de serviço executará a limpeza
        sobre a lista de arquivos retornada por este método.

        Args:
            id (UUID): Id do dado a ser removido.
            _db: (AsyncSession): Repasse de sessão.

        Returns:
            list: Lista com o conteúdo que os atributos de arquivos tinham para a camada service invocar.
        """
        try:
            exclude_files = []
            stmt = select(self).filter_by(id=id)
            result = await _db.execute(stmt)
            data = result.scalars().first()
            if not data:
                raise CustomException(
                    status_code=404, detail="Dado não encontrado"
                )

            await _db.delete(data)
            await _db.commit()

            return exclude_files
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def update(self, id: UUID, _db: AsyncSession, **json_data) -> object:
        """funçao para atuilizar dados de uma tabela a partir de um dict

        Args:
            id (UUID): UUID do dado a ser atualizado
            _db (AsyncSession): Sessão da conexão
        """
        try:
            stmt = select(self).filter_by(id=id)
            result = await _db.execute(stmt)
            data = result.scalars().first()
            if not data:
                raise CustomException(
                    status_code=404,
                    detail="Dado não encontrado",
                )
            for key, value in json_data.items():
                setattr(data, key, value)
            _db.add(data)
            await _db.commit()
            await _db.refresh(data)
            return data
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def update_form(self, id: UUID, _db: AsyncSession, **form) -> object:
        """funçao para atuilizar dados de uma tabela a partir de um dict

        Nota: Removeu-se as interações com sistema de arquivo (save_file/delete_file).
        No lugar, a camada externa deverá processar e apenas submeter o nome em arquivo em form.
        """
        try:
            stmt = select(self).filter_by(id=id)
            result = await _db.execute(stmt)
            data = result.scalars().first()
            if not data:
                raise CustomException(
                    status_code=404,
                    detail="Dado não encontrado",
                )

            for key, value in form.items():
                if value or str(type(value)) == "<class 'bool'>":
                    setattr(data, key, value)
            _db.add(data)
            await _db.commit()
            await _db.refresh(data)

            return data

        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def create_form(self, _db: AsyncSession, **form) -> object:
        """
        Nota: Exclusão física de arquivos isolada daqui. Camada Service processa "files" primeiro
        e transporta os nomes para form.
        """
        try:
            data = self()
            for key, value in form.items():
                if value:
                    setattr(data, key, value)
            _db.add(data)
            await _db.commit()
            await _db.refresh(data)
            return data

        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)

    @classmethod
    async def get(
        self,
        _db: AsyncSession,
        attribute: str | None = None,
        value: Any | None = None,
    ) -> object:
        """_summary_

        Args:
            attribute (str): _description_
            value (Any): _description_

        Returns:
            object: _description_
        """
        try:
            stmt = select(self).filter(getattr(self, attribute) == value)
            result = await _db.execute(stmt)
            data = result.scalars().first()

            return data
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseException(detail=str(e), status_code=500)
