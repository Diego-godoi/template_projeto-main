# Lista de Tarefas: Melhorias de Arquitetura e Padrões (V3 - Async Edition)

## Épico 1: Desacoplamento e Persistência Assíncrona
*Transição para `AsyncSession` e motor `asyncpg`.*

- [x] **1.1 Remover HTTPExceptions do ORM** 🟢
- [x] **1.2 Injeção de Sessão (DI) e Data Mapper** 🟢
- [x] **1.3 Isolar Efeitos Colaterais (I/O e Filesystem)** 🟢
- [x] **1.4 Migração para SQLAlchemy Async:** 🟢
    - Substituir `psycopg2` por `asyncpg` na URL de conexão (`postgresql+asyncpg://...`).
    - Trocar `create_engine` por `create_async_engine`.
    - Atualizar a factory de sessão para `async_sessionmaker` com `expire_on_commit=False`.
    - Refatorar o `get_db` (dependência do FastAPI) para ser um `async generator`.
- [x] **1.5 Refatoração de Métodos CRUD:** 🟢
    - Transformar todos os métodos da `BaseService` em `async def`.
    - Substituir chamadas `.first()`, `.all()` e `.execute()` por `await db.execute(...)` e `result.scalars()`.

---

## Épico 2: Separação de Preocupações (Pydantic x SQLAlchemy)
- [x] **2.1 Limpeza de Consultas DB em Schemas** 🟢

---

## Épico 3: Isolamento da Camada de Serviços
- [x] **3.1 Reorganização de Diretórios (Domain-Driven)** 🟢

---

## Épico 4: Segurança, Throttling e Performance
- [x] **4.1 Proteção contra Força Bruta (Rate Limiting)** 🟢
- [x] **4.2 Prevenção de Slow Queries (Tuning de ILIKE)** 🟢
- [x] **4.3 Monitoramento de Conexões Async:** 🟢
    - Configurar `pool_size` e `max_overflow` no `AsyncEngine` para evitar exaustão de conexões no Postgres em picos de concorrência.

---

## Épico 5: Fluxo de Automação de Testes (Async)
*Refatoração para suportar testes que não bloqueiam o loop de eventos.*

- [x] **5.1 Estruturação Base (conftest.py)** 🟢
- [x] **5.2 Refatorar Fixtures para Async:** 🟢
    - Atualizar a fixture `db_session` para ser `async` e utilizar `AsyncSession`.
    - Garantir que o `rollback` após cada teste seja feito via `await session.rollback()`.
- [x] **5.3 Async Test Client:** 🟢
    - Substituir o `TestClient` padrão do FastAPI pelo `httpx.AsyncClient` (essencial para testar endpoints `async def`).
- [x] **5.4 Cobertura E2E Assíncrona:** 🟢
    - Migrar os testes de `test_users_service.py` para usar `@pytest.mark.asyncio`.