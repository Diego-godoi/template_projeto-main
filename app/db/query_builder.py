from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Enum, String, Text, func, inspect, select
from sqlalchemy.dialects.postgresql import (  # troque pelo dialect do seu banco se necessário
    CHAR,
)
from sqlalchemy.orm import selectinload

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

    Responsabilidade única: montar o objeto select() com filtros, paginação,
    projeção de colunas e carregamento de relacionamentos. Nunca executa
    nada — o Service é dono do session.

    Uso:
        stmt = (
            QueryBuilder(User)
            .filter(attribute="name", value="joão", operator="~")
            .filter_json(json_string={"active": True})
            .include_only(["addresses"])
            .paginate(skip=0, limit=20)
            .build()
        )

        result = await session.execute(stmt)
        data = result.scalars().unique().all()
    """

    def __init__(self, model):
        self._model = model
        self._query = select(model)
        self._skip = None
        self._limit = None
        self._all_data = True
        self._order_field = None
        self._order_descending = True

    def set_all_data(self, all_data: bool) -> "QueryBuilder":
        """Define se deve retornar todos os resultados ou apenas o primeiro.

        Quando ``all_data`` é False, o build() força ``LIMIT 1``,
        sobrescrevendo qualquer paginação configurada.
        """
        self._all_data = all_data
        return self

    def order_by(
        self, field: str | None = None, descending: bool = True
    ) -> "QueryBuilder":
        """
        Define o atributo e direção de ordenação.
        """
        self._order_field = field
        self._order_descending = descending
        return self

    def join(self, target: Any, *props: Any) -> "QueryBuilder":
        """
        Adiciona um JOIN à query.
        """
        self._query = self._query.join(target, *props)
        return self

    def where(self, *criteria: Any) -> "QueryBuilder":
        """
        Adiciona cláusulas WHERE literais à query.
        """
        self._query = self._query.where(*criteria)
        return self

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
        parsed_value = self._coerce_value(column, value, operator)

        match operator:
            case "=":
                self._query = self._query.filter(column == parsed_value)

            case "~":
                self._validate_ilike_value(parsed_value)
                self._query = self._query.filter(
                    column.ilike(f"%{parsed_value}%")
                )

            case "!":
                self._query = self._query.filter(column != parsed_value)

            case "<":
                self._query = self._query.filter(column < parsed_value)

            case ">":
                self._query = self._query.filter(column > parsed_value)

            case "<=":
                self._query = self._query.filter(column <= parsed_value)

            case ">=":
                self._query = self._query.filter(column >= parsed_value)

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
            parsed_val = self._coerce_value(column, val, operator)

            match operator:
                case "=":
                    self._query = self._query.filter(column == parsed_val)

                case "~":
                    self._validate_column_is_text(field, column)
                    self._query = self._query.filter(
                        column.ilike(f"%{parsed_val}%")
                    )

                case _:
                    raise CustomException(
                        status_code=422,
                        detail=f"Operador '{operator}' não suportado para json_string.",
                    )

        return self

    # ------------------------------------------------------------------
    # Carregamento de relacionamentos (eager loading)
    # ------------------------------------------------------------------

    def include_only(self, fields: list[str] | None = None) -> "QueryBuilder":
        """
        Carrega relacionamentos do model via eager loading (`selectinload`).

        Cada item de `fields` deve ser o nome de um relacionamento definido
        no model (ex: "addresses"). Nomes que não correspondem a um
        relacionamento válido são silenciosamente ignorados — apenas os
        relacionamentos válidos são carregados.

        Não tem relação com colunas do próprio model — para projetar
        colunas, use `select_fields`.
        """
        if not fields:
            return self

        mapper = inspect(self._model)

        for field in fields:
            if field in mapper.relationships:
                self._query = self._query.options(
                    selectinload(getattr(self._model, field))
                )

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
        Guarda offset/limit para aplicação posterior no build().
        """
        self._skip = skip
        self._limit = limit
        return self

    # ------------------------------------------------------------------
    # Finalização
    # ------------------------------------------------------------------

    def build(self):
        """
        Retorna o objeto select() pronto para ser executado pelo Service.
        Aplica ordenação e paginação.
        """
        query = self._query

        # Aplicar ordenação explícita ou padrão
        if self._order_field and hasattr(self._model, self._order_field):
            column = getattr(self._model, self._order_field)
            query = query.order_by(
                column.desc() if self._order_descending else column.asc()
            )
        elif hasattr(self._model, "created_at"):
            query = query.order_by(self._model.created_at.desc())
        elif hasattr(self._model, "id"):
            query = query.order_by(self._model.id.desc())

        # Se all_data for False, força LIMIT 1 ignorando a paginação
        if not self._all_data:
            query = query.limit(1)
        elif self._skip is not None and self._limit is not None:
            query = query.offset(self._skip).limit(self._limit)

        return query

    def build_count(self):
        """
        Retorna a query de contagem (func.count) mantendo os mesmos filtros aplicados,
        sem offset, limit ou order_by.
        """
        count_target = getattr(self._model, "id", None)
        if count_target is not None:
            return self._query.with_only_columns(
                func.count(count_target)
            ).order_by(None)
        return self._query.with_only_columns(func.count()).order_by(None)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_value(column, value: Any, operator: str) -> Any:
        """Converte a string de entrada para o tipo Python adequado conforme a coluna."""
        if value is None or operator == "|":
            return value

        column_type = getattr(column, "type", None)

        if isinstance(column_type, Enum):
            enum_class = column_type.enum_class
            if enum_class is not None:
                try:
                    return enum_class(value)
                except ValueError:
                    valid_values = ", ".join(
                        str(enum_value.value) for enum_value in enum_class
                    )
                    raise CustomException(
                        status_code=422,
                        detail=(
                            f"O valor '{value}' não é válido para o Enum. "
                            f"Valores válidos: {valid_values}."
                        ),
                    )

        if isinstance(column_type, Boolean):
            val_str = str(value).strip().lower()
            if val_str in ("true", "t", "1", "yes"):
                return True
            if val_str in ("false", "f", "0", "no"):
                return False
            raise CustomException(
                status_code=422,
                detail=f"O valor '{value}' não é um booleano válido.",
            )

        return value

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
            lambda x: (
                datetime.strptime(x, "%Y-%m-%d")
                .replace(tzinfo=timezone.utc)
                .date()
            ),
            lambda x: (
                datetime.strptime(x, "%H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .time()
            ),
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
