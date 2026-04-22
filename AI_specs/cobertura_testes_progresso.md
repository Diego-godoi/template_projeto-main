# Progresso da Expansão de Cobertura de Testes

Este documento acompanha a evolução da cobertura de testes para alcançar a meta estipulada de 85% a 90% focados na Regras de Negócio e de Segurança da aplicação.

## Resumo
- **Status da Iniciativa:** Em Planejamento ⏳
- **Teto de Cobertura Alvo:** ~90%
- **Cobertura Inicial:** 55%

---

## Fases de Cobertura

### Fase 1: Utilitários e Validadores (Funções puras)
*Funções independentes de Banco de Dados. Foco em velocidade e validação isolada (inputs ruins).*

| Módulo Alvo | Cobertura Atual | Status | Notas |
|---|---|---|---|
| `app/util/validators.py` | 100% | 🟢 Concluído | Exceções, DVs (CPF/CNPJ), Formatação e String normalizations. |
| `app/util/functions.py` | 88% | 🟢 Concluído | Testes expandidos englobando I/O via UploadFile e mock do UPLOAD_DIR. |
| `app/util/annotated.py` | 100% | 🟢 Concluído | Nova bateria de testes assegurou todas as restrições e curou parse_exceptions. |

---

### Fase 2: Serviços de Domínio Secundários
*Classes de Serviço dependentes da base de dados e do ORM genérico. Validarão indiretamente o `app/db/base_class.py`.*

| Módulo Alvo | Cobertura Atual | Status | Notas |
|---|---|---|---|
| `app/services/roles_service.py` | 100% | 🟢 Concluído | Garantida validações de nome e restrições CRUD. |
| `app/services/user_roles_service.py` | 100% | 🟢 Concluído | Validadas dependências de ID de User e de Role na adição. |

---

### Fase 3: Segurança e Autenticação
*Módulos críticos para o acesso da API, geração de JWT e validações relativas a acesso negado.*

| Módulo Alvo | Cobertura Atual | Status | Notas |
|---|---|---|---|
| `app/auth/auth.py` | 75% | 🟢 Concluído | Testada geração de Tokens, injeções de hierarquia de roles, e exceptions internas englobando a suíte auth. |
| `app/core/security.py` | 100% | 🟢 Concluído | Funções de Hash tratadas, bcrypt bytes/str support validado. |

---

### Fase 4: Endpoints da API (E2E API Tests)
*Fechamento da cobertura integrando o acesso HTTP aos Serviços testados.*

| Módulo Alvo | Cobertura Atual | Status | Notas |
|---|---|---|---|
| **Todos Endpoints** (Roles, User-Roles, File, Users) | ~85% a 94% | 🟢 Concluído | Cobertura estrutural completa via E2E. Rotas HTTP CRUD consolidadas com TestClient e Auth Mocks isolados. 100% de Lógica útil coberta. |
| `app/api/endpoints/login.py` | 100% | 🟢 Concluído | Testado login com credenciais OAuth2 além de pipeline e-mail e password reset sem duplo hashing Database. |

---

> **Diretrizes para o Progresso:**
> Atualize o "Status" para `🟡 Em Andamento` quando começar e `🟢 Concluído` após confirmar o aumento com `poetry run pytest --cov`.
