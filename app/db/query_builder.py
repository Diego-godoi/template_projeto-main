from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, func, select
from sqlalchemy.dialects.postgresql import (  # troque pelo dialect do seu banco se necessário
    CHAR,
)
from sqlalchemy.orm import load_only

from app.error import CustomException


class ServiceResponse:
    """Envelope padronizado de retorno da camada de Service para listagens.

    Encapsula os dados (`data`) e metadados de paginação (`meta`) em
    atributos legíveis pelo Pydantic via `from_attributes=True`.

    Attributes:
        data: Lista de objetos ORM retornados pela query.
        meta: Dicionário com metadados (ex: ``{"total_items": 42}``).
    """

    def __init__(self, data: Any, meta: dict | None = None) -> None:
        self.data = data
        self.meta = meta if meta is not None else {}


class QueryBuilder:
    """
    Construtor de queries SQLAlchemy.

    Responsabilidade única: montar o objeto select() com filtros, paginação
    e projeção de colunas. Nunca executa nada — o Service é dono do session.

    Uso:
        stmt = (
            QueryBuilder(User)
            .filter(attribute="name", value="joão", operator="~")
            .filter_json(json_string={"active": True})
            .include_only(["id", "name", "email"])
            .paginate(skip=0, limit=20)
            .build()
        )

        result = await session.execute(stmt)
        data = result.scalars().unique().all()
    """

    def __init__(self, model):
        self._model = model
        self._query = select(model)

    # ------------------------------------------------------------------
    # Filtro simples: attribute + value + operator
    # ------------------------------------------------------------------

    def filter(
        self,
        attribute: str | None = None,
        value: str | None = None,
        operator: str = "=",
    ) -> "QueryBuilder":
        """
        Aplica um filtro simples de coluna.

        Operadores suportados:
            =   igualdade exata
            ~   ILIKE (busca parcial case-insensitive)
            !   diferente
            <   menor que
            >   maior que
            <=  menor ou igual
            >=  maior ou igual
            |   intervalo (value deve ser "lower|upper")
        """
        if attribute is None or value is None:
            return self

        self._validate_attribute(attribute)
        column = getattr(self._model, attribute)

        match operator:
            case "=":
                self._query = self._query.filter(column == value)

            case "~":
                self._validate_ilike_value(value)
                self._query = self._query.filter(column.ilike(f"%{value}%"))

            case "!":
                self._query = self._query.filter(column != value)

            case "<":
                self._query = self._query.filter(column < value)

            case ">":
                self._query = self._query.filter(column > value)

            case "<=":
                self._query = self._query.filter(column <= value)

            case ">=":
                self._query = self._query.filter(column >= value)

            case "|":
                lower_value, upper_value = self._parse_range(value)
                self._query = self._query.filter(
                    column.between(lower_value, upper_value)
                )

            case _:
                raise CustomException(
                    status_code=422,
                    detail=f"Operador '{operator}' não suportado.",
                )

        return self

    # ------------------------------------------------------------------
    # Filtro múltiplo: json_string (dict campo → valor)
    # ------------------------------------------------------------------

    def filter_json(
        self,
        json_string: dict | None = None,
        operator: str = "=",
    ) -> "QueryBuilder":
        """
        Aplica filtros a partir de um dicionário campo → valor.

        Operadores suportados: = e ~.
        """
        if not json_string:
            return self

        invalid_fields = [
            field for field in json_string if not hasattr(self._model, field)
        ]
        if invalid_fields:
            raise CustomException(
                status_code=404,
                detail=(
                    f"Os campos '{', '.join(invalid_fields)}' não foram encontrados "
                    f"na tabela '{self._model.__tablename__}'."
                ),
            )

        for field, val in json_string.items():
            column = getattr(self._model, field)

            match operator:
                case "=":
                    self._query = self._query.filter(column == val)

                case "~":
                    self._validate_column_is_text(field, column)
                    self._query = self._query.filter(column.ilike(f"%{val}%"))

                case _:
                    raise CustomException(
                        status_code=422,
                        detail=f"Operador '{operator}' não suportado para json_string.",
                    )

        return self

    # ------------------------------------------------------------------
    # Projeção de colunas
    # ------------------------------------------------------------------

    def include_only(self, fields: list[str] | None = None) -> "QueryBuilder":
        """
        Limita as colunas carregadas (load_only).
        Campos inválidos são silenciosamente ignorados.
        """
        if not fields:
            return self

        columns = [
            getattr(self._model, col)
            for col in fields
            if hasattr(self._model, col)
        ]
        if columns:
            self._query = self._query.options(load_only(*columns))

        return self

    # ------------------------------------------------------------------
    # Paginação
    # ------------------------------------------------------------------

    def paginate(
        self,
        skip: int | None = None,
        limit: int | None = None,
    ) -> "QueryBuilder":
        """
        Aplica offset/limit. Só é aplicado quando ambos são fornecidos.
        """
        if skip is not None and limit is not None:
            self._query = self._query.offset(skip * limit).limit(limit)

        return self

    # ------------------------------------------------------------------
    # Finalização
    # ------------------------------------------------------------------

    def build(self):
        """
        Retorna o objeto select() pronto para ser executado pelo Service.
        Nunca toca no session — execução é responsabilidade de quem chamou.
        """
        return self._query

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _validate_attribute(self, attribute: str) -> None:
        if not hasattr(self._model, attribute):
            raise CustomException(
                status_code=404,
                detail=(
                    f"Atributo '{attribute}' não encontrado "
                    f"na tabela '{self._model.__tablename__}'."
                ),
            )

    @staticmethod
    def _validate_ilike_value(value: str) -> None:
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

    @staticmethod
    def _validate_column_is_text(field: str, column) -> None:
        attribute_type = column.property.columns[0].type
        if not isinstance(attribute_type, (String, Text, CHAR)):
            raise CustomException(
                status_code=422,
                detail=(
                    f"O operador ILIKE não pode ser aplicado ao tipo de dados "
                    f"do atributo '{field}'."
                ),
            )

    @staticmethod
    def _parse_range(value: str) -> tuple:
        """
        Recebe "lower|upper" e tenta converter para int, float, date ou time.
        Levanta CustomException se nenhum tipo funcionar.
        """
        try:
            lower, upper = value.split("|")
        except ValueError:
            raise CustomException(
                status_code=422,
                detail="O intervalo deve estar no formato 'lower|upper'.",
            )

        converters = [
            int,
            float,
            lambda x: datetime.strptime(x, "%Y-%m-%d").date(),
            lambda x: datetime.strptime(x, "%H:%M:%S").time(),
        ]

        for convert in converters:
            try:
                return convert(lower), convert(upper)
            except (ValueError, TypeError):
                continue

        raise CustomException(
            status_code=422,
            detail=(
                "O intervalo deve estar em um formato compatível "
                "com inteiros, floats, datas ou tempos."
            ),
        )
