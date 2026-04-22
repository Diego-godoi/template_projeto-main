# Lista de Tarefas: Melhorias de Arquitetura e Padrões

Este documento traduz a análise mais recente de aderência ao "Template Base" em tarefas acionáveis e graduais.

## Épico 1: Desacoplamento do Banco de Dados (`base_class.py` e SQLAlchemy)
*O ORM não deve conhecer o contexto HTTP nem o file system do SO.*

- [ ] **1.1 Remover HTTPExceptions do ORM:**
  - Em `app/db/base_class.py`, substituir todos os `raise custom_HTTPException(e)` por exceções genéricas customizadas (ex: `DatabaseException` ou relançar o erro original do DB).
  - Adicionar um Exception Handler no `app/main.py` para capturar `DatabaseException` (ou `SQLAlchemyError`) e convertê-los em Retornos HTTP 500/400 (Isolando a camada FastAPI da camada DB).
- [ ] **1.2 Injeção de Sessão Transacional (Dependency Injection):**
  - Remover as instâncias puras locais `_db = SessionLocal()` de dentro dos métodos CRUD do `base_class.py`. 
  - Exigir que a `session: Session` seja injetada por parâmetro a partir da camada Service/Endpoint para garantir coesão em transações complexas e facilidade no *mocking* com Pytest.
- [ ] **1.3 Isolar Efeitos Colaterais (I/O e Filesystem):**
  - O método `remove_data_and_files` possui importações de manipulação de disco (`delete_file(core.settings.UPLOAD_DIR, ...)`). Modificar para que a `base_class` remova apenas o registro no banco, e os arquivos físicos sejam excluídos pela camada `Service`.

## Épico 2: Separação de Preocupações (Pydantic x SQLAlchemy)
*Schemas de transição de dados devem ser "burros". Eles validam dados soltos, não o estado do banco.*

- [ ] **2.1 Limpeza de Consultas DB em Schemas:**
  - No arquivo `app/schema/users_schema.py` (e correlatos, se houver), remover chamadas bloqueantes `models.Users.get("email", data["email"])` feitas no `@model_validator`.
  - Transferir essas validações de integridade e unicidade para o fluxo do `UsersService.create_user()` e afins, lidando com eles antes do `.commit()` da transação.

## Épico 3: Isolamento da Camada de Serviços
*Serviços representam o domínio da aplicação. Eles não devem ser submetidos à infraestrutura da API HTTP.*

- [ ] **3.1 Reorganização de Diretórios (Domain-Driven):**
  - Mover `app/api/services/` para uma raiz segura, como `app/services/`.
  - Atualizar os imports em `app/api/endpoints/` para apontar para a nova arquitetura do diretório.

## Épico 4: Segurança, Throttling e Performance

- [ ] **4.1 Proteção contra Força Bruta (Rate Limiting):**
  - Integração da biblioteca `slowapi` no `app/main.py`.
  - Aplicação do limitador via `@limiter.limit("5/minute")` nos endpoints críticos: `/login` (auth.py/login.py) e recuperação de senha.
- [ ] **4.2 Prevenção de Slow Queries (Tuning de ILIKE):**
  - Revisar a aplicação indiscriminada do operador `~` (.ilike) acoplado a `%value%` no método `query_params` (e `query_by_partial_match`) do `base_class.py`. Proteger o input ou limitar o tamanho das strings para evitar surtos de CPU.

## Épico 5: Fluxo de Automação de Testes
*A raiz do "Template Base" exige um ambiente altamente coberto por integrações garantidas pelo Pytest.*

- [x] **5.1 Estruturação Base (conftest.py):**
  - Adicionar `pytest` caso fora da automação principal.
  - Implementar um `tests/conftest.py` contendo as *Fixtures* do FastAPI TestClient e injeção do mock da Sessão Temporária (Transações em Rollback).
- [x] **5.2 Cobertura de Ponta-a-Ponta (CRUD e Services):**
  - Criar testes espelhos da camada Service, começando por `tests/test_users_service.py` ou `tests/api/test_users.py`.
