# Análise de Arquitetura e Padrões de Projeto (V3 - Async & Data Mapper)

Este documento detalha os padrões arquiteturais e de design implementados no backend, focando em alta performance através de concorrência assíncrona e desacoplamento rigoroso.

## 1. Arquitetura Geral

O projeto utiliza uma arquitetura em camadas horizontais, movida pelo motor **FastAPI** com suporte total a **AsyncIO**, utilizando **PostgreSQL** via driver **asyncpg**.

- **Controllers (Rotas)**: Localizados em `app/api/endpoints/`. São assíncronos e têm responsabilidade única: gerir o tráfego HTTP, extrair dependências (`Depends`) e delegar a execução para a camada de serviço.
- **Service Layer (Camada de Serviço)**: Localizada em **`app/services/`** (raiz). É o núcleo da aplicação. Concentra a lógica de negócios e as transações de banco de dados, utilizando o padrão **Data Mapper**.
- **Modelos (Entities)**: Em `app/models/`. Representam apenas a estrutura relacional do SQLAlchemy. São objetos passivos que não possuem métodos de persistência.
- **Schemas (DTOs)**: Em `app/schema/`. Contratos Pydantic que garantem a integridade dos dados de entrada e a padronização das respostas JSON.

---

## 2. Padrões de Projeto e Engenharia

### 2.1. Concorrência Assíncrona (Async/Await)
Toda a pilha de I/O é não-bloqueante. Utilizamos `AsyncSession` do SQLAlchemy 2.0 para garantir que o banco de dados não gere gargalos no *Event Loop* do FastAPI.
> **Regra de Ouro:** Todas as chamadas ao banco ou sistema de arquivos devem ser precedidas por `await`.

### 2.2. Data Mapper
Substituímos o padrão *Active Record*. As entidades do banco não se auto-gerenciam. A lógica de persistência e consultas complexas (`select`, `scalars`) reside exclusivamente nos métodos assíncronos dos **Services**. Isso permite testar a lógica de negócio de forma isolada e facilita a migração de drivers de banco.

### 2.3. Unit of Work & Injeção de Sessão
A `AsyncSession` é injetada via dependência no Controller e repassada ao Serviço. Isso garante que múltiplas operações de banco dentro de um mesmo fluxo de negócio compartilhem a mesma transação, permitindo `commit` ou `rollback` atômicos.

### 2.4. Global Exception Handling
O backend não utiliza `HTTPException` nas camadas de serviço ou banco.
- As camadas inferiores lançam **Exceções de Domínio** customizadas.
- O `app/main.py` utiliza um `exception_handler` para capturar essas exceções e traduzi-las em status HTTP adequados, mantendo o código limpo e desacoplado.

---

## 3. Diretrizes de Segurança e Escalabilidade

### 3.1. Throttling e Proteção de Infraestrutura
- **Rate Limiting:** Implementado via `slowapi` em rotas críticas (Login, Password Reset) para prevenir ataques de força bruta.
- **Sanitização de Consultas:** Validação rigorosa de inputs em operadores `ILIKE` para evitar ataques de negação de serviço (DoS) via sobrecarga de processamento de texto no PostgreSQL.

### 3.2. Isolamento de Efeitos Colaterais
Operações de sistema (I/O de arquivos, chamadas para APIs de terceiros) são executadas de forma assíncrona apenas na camada de **Serviço** ou **Utils**, nunca nos modelos ou rotas.

### 3.3. Automação de Testes (Async Testing)
A suíte de testes em `pytest` opera em modo assíncrono (`pytest-asyncio`). Utilizamos o `httpx.AsyncClient` para testes de integração e garantimos que cada teste rode em uma transação isolada com *rollback* automático, mantendo o banco de testes sempre limpo.

---

## 4. Pilha Tecnológica
* **Web:** FastAPI (Async)
* **DB Engine:** SQLAlchemy 2.0 + `asyncpg`
* **Migrations:** Alembic
* **Validation:** Pydantic V2
* **Testing:** Pytest (Asyncio mode)
* **Rate Limit:** SlowAPI (Fixed-window)

---

### Observação para IAs de Automação:
Qualquer código gerado para este ecossistema **deve** seguir a estrutura de pastas `app/services/` e utilizar exclusivamente métodos assíncronos para persistência e validação de dados. O uso de `db.add()`, `db.commit()` e `db.refresh()` deve ser sempre `await`.