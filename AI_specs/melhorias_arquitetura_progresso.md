# Progresso das Melhorias de Arquitetura

Este documento acompanha o estado de implementação das tarefas listadas em `melhorias_arquitetura_tarefas.md`. Atualize os status conforme as refatorações forem aplicadas.

## Resumo Geral
- **Total de Épicos:** 5
- **Status Geral:** Em Planejamento ⏳

---

## Detalhamento por Épico

### Épico 1: Desacoplamento do Banco de Dados (`base_class.py`)
| Tarefa | Status | Notas |
|---|---|---|
| **1.1** Remover HTTPExceptions do ORM | 🟢 Concluído | Nova `DatabaseException` substituindo `custom_HTTPException` na `base_class.py` e capturada no `main.py`. |
| **1.2** Injeção de Sessão (DI) nas rotas/DB | 🟢 Concluído | Instâncias de `SessionLocal()` removidas! Transações (como `query_params`) agora forçam recebimento dinâmico de `_db`. |
| **1.3** Isolar Efeitos Colaterais (Remover files no Service) | 🟢 Concluído | I/O apagados da `base_class.py` em métodos como `remove_data`. |

---

### Épico 2: Separação Pydantic x SQLAlchemy
| Tarefa | Status | Notas |
|---|---|---|
| **2.1** Isolar BD de Schemas | 🟢 Concluído | Validadores retirados de `roles_schema`, `users_schema`. Inclusos no Create/Patch em `users_service`, `roles_service` e `user_roles_service`. |

---

### Épico 3: Isolamento da Camada de Serviços
| Tarefa | Status | Notas |
|---|---|---|
| **3.1** Reorganização de Diretórios | � Concluído | Diretório `app/api/services` fisicamente movido para `app/services` e imports ajustados em todos os `endpoints`. |

---

### Épico 4: Segurança, Throttling e Performance
| Tarefa | Status | Notas |
|---|---|---|
| **4.1** Proteção de Rotas com Rate Limiting (`slowapi`) | 🟢 Concluído | `slowapi` instalado. `Limiter` isolado em `app/core/limiter.py`. Limites: `5/minute` em `/login/access-token`, `3/minute` em `/forgot-my-password/`. Em produção com proxy reverso, mover para Nginx. |
| **4.2** Sanitização de Input no operador ILIKE | 🟢 Concluído | Validação de 3–100 chars adicionada em `query_by_partial_match` e no operador `~` de `query_params` no `base_class.py`. Retorna HTTP 422 com mensagem descritiva ao violar limites. |
| **4.3** *(Novo)* Nota arquitetural: ILIKE em produção de escala | 🔵 Backlog | Para conjuntos de dados acima de ~100k registros, criar índice trigram (`pg_trgm`) no PostgreSQL para colunas texto alvo de buscas parciais. Requer script de migration Alembic manual. |

---

### Épico 5: Fluxo de Automação de Testes
| Tarefa | Status | Notas |
|---|---|---|
| **5.1** Estruturação Base (`conftest.py`) | 🟢 Concluído | Criada configuração do banco transacional via `engine_test` e `db_session` com rollback, além de client FastAPI com injeção de dependência via `dependency_overrides`. |
| **5.2** Modelos de Cobertura E2E (Users/Services) | 🟢 Concluído | Criados testes espelhos da camada Service em `tests/test_users_service.py` e testes E2E em `tests/test_users_api.py`. Implementação estável utilizando o Faker e resolvendo restrições de validação de e-mails (`email_validator`). |

---

> **Como utilizar este documento:**
> 1. Inicie um Épico mudando o status para `🟡 Em Andamento`.
> 2. Ao finalizar PR ou Commit, altere para `🟢 Concluído`.
> 3. Deixe observações nas Notas em caso de gargalos arquiteturais.
