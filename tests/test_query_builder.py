# tests/test_query_builder.py
"""
Testes unitários do QueryBuilder e ServiceResponse (app/db/query_builder.py).

O QueryBuilder é síncrono (apenas monta statements), então os testes
de construção de query NÃO precisam de async nem de banco de dados.
Testes de integração (execução real) usam a fixture `async_db_session`.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import error, models
from app.db.query_builder import QueryBuilder, ServiceResponse

# ---------------------------------------------------------------------------
# ServiceResponse
# ---------------------------------------------------------------------------


class TestServiceResponse:
    """Testes do envelope ServiceResponse."""

    def test_cria_service_response_com_dados_e_meta(self):
        """ServiceResponse deve armazenar data e meta corretamente."""
        dados = [1, 2, 3]
        meta = {"total_items": 3}
        resp = ServiceResponse(data=dados, meta=meta)

        assert resp.data == dados
        assert resp.meta == meta

    def test_cria_service_response_sem_meta_usa_dict_vazio(self):
        """Quando meta não é fornecido, deve defaultar para dict vazio."""
        resp = ServiceResponse(data=[])

        assert resp.data == []
        assert resp.meta == {}

    def test_cria_service_response_com_meta_none_usa_dict_vazio(self):
        """Quando meta=None é passado explicitamente, deve usar dict vazio."""
        resp = ServiceResponse(data=[], meta=None)

        assert resp.meta == {}


# ---------------------------------------------------------------------------
# QueryBuilder — Construção de Queries (Unitário, sem banco)
# ---------------------------------------------------------------------------


class TestQueryBuilderFilter:
    """Testes do método .filter() do QueryBuilder."""

    def test_filter_sem_parametros_retorna_query_inalterada(self):
        """Chamar .filter() sem attribute/value não deve alterar a query."""
        qb = QueryBuilder(models.Users)
        stmt_original = str(qb.build().compile())

        stmt_filtrado = str(qb.filter().build().compile())

        assert stmt_original == stmt_filtrado

    def test_filter_igualdade_aplica_where(self):
        """Operador '=' deve gerar cláusula WHERE com igualdade."""
        stmt = (
            QueryBuilder(models.Users)
            .filter(attribute="email", value="test@test.com", operator="=")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "users.email = 'test@test.com'" in sql

    def test_filter_ilike_aplica_ilike(self):
        """Operador '~' deve gerar cláusula ILIKE (ou LOWER/LIKE equivalente)."""
        stmt = (
            QueryBuilder(models.Users)
            .filter(attribute="email", value="test@test.com", operator="~")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        # SQLAlchemy compila .ilike() como LOWER(col) LIKE LOWER(val)
        # no dialect genérico, ou ILIKE no PostgreSQL.
        assert "LIKE" in sql.upper()
        assert "%test@test.com%" in sql

    def test_filter_diferente_aplica_not_equal(self):
        """Operador '!' deve gerar cláusula WHERE com desigualdade."""
        stmt = (
            QueryBuilder(models.Users)
            .filter(attribute="email", value="x@x.com", operator="!")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "users.email != 'x@x.com'" in sql

    def test_filter_operador_invalido_levanta_custom_exception(self):
        """Operador desconhecido deve lançar CustomException 422."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter(
                attribute="email", value="x", operator="$$$"
            )

        assert exc_info.value.status_code == 422

    def test_filter_atributo_inexistente_levanta_custom_exception(self):
        """Atributo que não existe no modelo deve lançar CustomException 404."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter(
                attribute="campo_fantasma", value="x", operator="="
            )

        assert exc_info.value.status_code == 404


class TestQueryBuilderFilterIlikeValidacao:
    """Testes das validações específicas do operador ILIKE (~)."""

    def test_ilike_valor_muito_curto_levanta_422(self):
        """Valor com menos de 3 caracteres no ILIKE deve lançar 422."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter(
                attribute="email", value="ab", operator="~"
            )

        assert exc_info.value.status_code == 422
        assert "mínimo 3" in exc_info.value.detail

    def test_ilike_valor_muito_longo_levanta_422(self):
        """Valor com mais de 100 caracteres no ILIKE deve lançar 422."""
        valor_longo = "x" * 101

        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter(
                attribute="email", value=valor_longo, operator="~"
            )

        assert exc_info.value.status_code == 422
        assert "100 caracteres" in exc_info.value.detail


class TestQueryBuilderFilterJson:
    """Testes do método .filter_json() do QueryBuilder."""

    def test_filter_json_none_retorna_query_inalterada(self):
        """Chamar .filter_json(None) não deve alterar a query."""
        qb = QueryBuilder(models.Users)
        stmt_original = str(qb.build().compile())

        stmt_filtrado = str(qb.filter_json(None).build().compile())

        assert stmt_original == stmt_filtrado

    def test_filter_json_com_campo_valido_aplica_where(self):
        """filter_json com campo existente deve gerar cláusula WHERE."""
        stmt = (
            QueryBuilder(models.Users)
            .filter_json({"active": True}, operator="=")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "active" in sql

    def test_filter_json_campo_inexistente_levanta_custom_exception(self):
        """Campo que não existe no modelo deve lançar CustomException 404."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter_json(
                {"campo_inexistente": "valor"}
            )

        assert exc_info.value.status_code == 404
        assert "campo_inexistente" in exc_info.value.detail

    def test_filter_json_operador_invalido_levanta_422(self):
        """Operador diferente de '=' e '~' deve lançar 422."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter_json(
                {"email": "x"}, operator=">"
            )

        assert exc_info.value.status_code == 422


class TestQueryBuilderPaginate:
    """Testes do método .paginate() do QueryBuilder."""

    def test_paginate_com_skip_e_limit_aplica_offset_e_limit(self):
        """Paginate com skip=1, limit=10 deve gerar OFFSET 10 LIMIT 10."""
        stmt = QueryBuilder(models.Users).paginate(skip=1, limit=10).build()
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "LIMIT" in sql.upper()
        assert "OFFSET" in sql.upper()

    def test_paginate_sem_parametros_nao_altera_query(self):
        """Paginate sem skip/limit não deve adicionar OFFSET/LIMIT."""
        qb = QueryBuilder(models.Users)
        stmt_original = str(qb.build().compile())

        stmt_paginado = str(qb.paginate().build().compile())

        assert stmt_original == stmt_paginado

    def test_paginate_somente_skip_sem_limit_nao_altera_query(self):
        """Paginate com skip mas sem limit não deve aplicar paginação."""
        qb = QueryBuilder(models.Users)
        stmt_original = str(qb.build().compile())

        stmt_paginado = str(qb.paginate(skip=1).build().compile())

        assert stmt_original == stmt_paginado


class TestQueryBuilderIncludeOnly:
    """Testes do método .include_only() do QueryBuilder."""

    def test_include_only_com_campos_validos_aplica_load_only(self):
        """include_only com campos existentes deve gerar load_only no statement."""
        stmt = (
            QueryBuilder(models.Users)
            .include_only(["profiles", "user_roles"])
            .build()
        )
        # Verifica se a opção load_only está presente nas options do statement
        assert len(stmt._with_options) > 0

    def test_include_only_sem_campos_nao_altera_query(self):
        """include_only com lista vazia ou None não deve alterar a query."""
        stmt_none = QueryBuilder(models.Users).include_only(None).build()
        stmt_vazio = QueryBuilder(models.Users).include_only([]).build()

        assert len(stmt_none._with_options) == 0
        assert len(stmt_vazio._with_options) == 0

    def test_include_only_campos_inexistentes_sao_ignorados(self):
        """Campos que não existem no modelo devem ser silenciosamente ignorados."""
        stmt = (
            QueryBuilder(models.Users).include_only(["campo_fantasma"]).build()
        )
        # Sem campos válidos → nenhuma opção adicionada
        assert len(stmt._with_options) == 0


class TestQueryBuilderChaining:
    """Testes de encadeamento fluente (method chaining)."""

    def test_encadeamento_completo_gera_query_valida(self):
        """Filter + filter_json + include_only + paginate devem encadear."""
        stmt = (
            QueryBuilder(models.Users)
            .filter(attribute="email", value="test@x.com", operator="=")
            .filter_json({"active": True})
            .include_only(["id", "email"])
            .paginate(skip=0, limit=10)
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "email" in sql
        assert "active" in sql
        assert "LIMIT" in sql.upper()


class TestQueryBuilderRangeFilter:
    """Testes do operador de intervalo '|'."""

    def test_range_inteiro_aplica_between(self):
        """Operador '|' com inteiros deve gerar BETWEEN."""
        stmt = (
            QueryBuilder(models.Roles)
            .filter(attribute="name", value="1|10", operator="|")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "BETWEEN" in sql.upper()

    def test_range_formato_invalido_levanta_422(self):
        """Valor sem separador '|' deve lançar CustomException 422."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Roles).filter(
                attribute="name", value="sem_separador", operator="|"
            )

        assert exc_info.value.status_code == 422

    def test_range_tipo_incompativel_levanta_422(self):
        """Valor que não converte para nenhum tipo suportado deve lançar 422."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Roles).filter(
                attribute="name", value="abc|def", operator="|"
            )

        assert exc_info.value.status_code == 422


class TestQueryBuilderComparisonOperators:
    """Testes dos operadores de comparação <, >, <=, >=."""

    def test_filter_menor_que_aplica_where(self):
        """Operador '<' deve gerar cláusula WHERE com menor que."""
        stmt = (
            QueryBuilder(models.Roles)
            .filter(attribute="name", value="Z", operator="<")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "roles.name < 'Z'" in sql

    def test_filter_maior_que_aplica_where(self):
        """Operador '>' deve gerar cláusula WHERE com maior que."""
        stmt = (
            QueryBuilder(models.Roles)
            .filter(attribute="name", value="A", operator=">")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "roles.name > 'A'" in sql

    def test_filter_menor_ou_igual_aplica_where(self):
        """Operador '<=' deve gerar cláusula WHERE com menor ou igual."""
        stmt = (
            QueryBuilder(models.Roles)
            .filter(attribute="name", value="M", operator="<=")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "roles.name <= 'M'" in sql

    def test_filter_maior_ou_igual_aplica_where(self):
        """Operador '>=' deve gerar cláusula WHERE com maior ou igual."""
        stmt = (
            QueryBuilder(models.Roles)
            .filter(attribute="name", value="M", operator=">=")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "roles.name >= 'M'" in sql


class TestQueryBuilderFilterJsonIlike:
    """Testes do filter_json com operador ILIKE em colunas de texto e não-texto."""

    def test_filter_json_ilike_coluna_texto_funciona(self):
        """ILIKE em coluna String deve funcionar normalmente."""
        stmt = (
            QueryBuilder(models.Roles)
            .filter_json({"name": "admin"}, operator="~")
            .build()
        )
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "LIKE" in sql.upper()
        assert "%admin%" in sql

    def test_filter_json_ilike_coluna_nao_texto_levanta_422(self):
        """ILIKE em coluna booleana deve lançar CustomException 422."""
        with pytest.raises(error.CustomException) as exc_info:
            QueryBuilder(models.Users).filter_json(
                {"active": "true"}, operator="~"
            )

        assert exc_info.value.status_code == 422
        assert "ILIKE" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Testes de integração — execução real contra o banco de testes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_builder_executa_busca_no_banco(
    async_db_session: AsyncSession,
):
    """QueryBuilder deve gerar um statement executável pelo session.execute()."""
    stmt = QueryBuilder(models.Users).paginate(skip=0, limit=5).build()

    result = await async_db_session.execute(stmt)
    data = result.scalars().unique().all()

    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_service_response_compativel_com_pydantic(
    async_db_session: AsyncSession,
):
    """ServiceResponse retornado pelo service deve ser serializável
    pelo schema Pydantic com from_attributes=True."""
    from app.schema import ResponseUsers

    stmt = QueryBuilder(models.Users).build()
    data = (await async_db_session.execute(stmt)).scalars().unique().all()
    meta = {"total_items": len(data)}

    response = ServiceResponse(data=data, meta=meta)

    # Deve serializar sem erro
    serialized = ResponseUsers.model_validate(response, from_attributes=True)

    assert isinstance(serialized.data, list)
    assert serialized.meta.total_items == len(data)
