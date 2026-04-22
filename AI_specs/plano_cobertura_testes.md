# Plano Diretor: Panorama e Cobertura de Testes

*Data de Análise: 16 de Abril de 2026*

Este documento traça o panorama em relação à suíte de testes do projeto Backend, baseado em uma análise de cobertura (Coverage) originada após a consolidação do Épico 5 (Configuração Base de Testes).

---

## 1. Fotografia Atual do Projeto

Atualmente, o projeto possui uma **cobertura geral de 55%**. 
O avanço já feito na infraestrutura (`conftest.py` transacional com bando isolado) e os recentes testes no modelo de "Users" elevaram significativamente a média, porém há déficits latentes nas frentes de utilitários e serviços pendentes.

**Visão Geral (Top 5 Defasagens):**
1. `app/db/base_class.py` - **28% de cobertura** (É a fundação do ORM do sistema)
2. `app/auth/auth.py` - **37% de cobertura** (Core de segurança e permissão de níveis)
3. `app/services/roles_service.py` - **32% de cobertura**
4. `app/services/user_roles_service.py` - **31% de cobertura**
5. `app/util/functions.py` / `validators.py` - **< 45% de cobertura**

---

## 2. O Que É Prioritário Testar (Onde o valor reside)

O desenvolvimento dos testes deve ser guiado em prol da blindagem das regras de negócio. Onde o sistema pensa, atua ou restringe as bordas:

*   **Camada de Serviços (`app/services/`)**: Centraliza as lógicas CRUD e de agregação e é livre de protocolos HTTP. É obrigatório criar um `test_[nome]_service.py` para espelhar as validações, limites e permissões manipuladas aqui. *(Meta: 90%+)*
*   **A Classe Base do Banco (`app/db/base_class.py`)**: Por ser uma arquitetura customizada poderosa (trata queries híbridas com `query_params`, operadores lógicos customizados `<`, `|`, e validações `islike`), este arquivo detém os métodos CRUD subjacentes. A recomendação aqui não é testar diretamente (já que é genérico), mas garantir que as operações dos *Services* causem a movimentação dessas lógicas. *(Meta via Tabela de Serviços: 80%+)*
*   **Utilitários e Validadores (`app/util/`)**: Funções vitais, puras e isoladas (`validate_cpf`, `validate_cnpj`, `normalize_email`, funções de datas e math). Podem ser os testes unitários mais simples da aplicação e geram altíssima garantia contra regressão. *(Meta: 95%+)*
*   **Core de Segurança (`app/auth/auth.py` e `app/core/security.py`)**: Lógica crítica sobre hierarquia (Keys N1 a N5), hashing de senhas via bcrypt, validações JWT e restrições de payload. Se isto falhar, abre brecha ao projeto inteiro. *(Meta: 90%+)*
*   **API / Endpoints (`app/api/endpoints/`)**: Aqui foca-se apenas **Rotas End-to-End (E2E)**. Não para testar a regra (que já estará testada no Service), mas sim para validar retornos HTTP (`200`, `201`, `422`, `401`), autenticação correta de sessão e serialização Pydantic. Pelo menos o "caminho feliz" e as reações às `CustomException` ou `ValidationException`. *(Meta: 80%+)*

---

## 3. O Que NÃO Faria Sentido Testar Intensivemente (E o porquê)

Em aplicações arquiteturalmente robustas como esta, baseada no FastAPI, não se recomenda o desperdício de esforço nos seguintes itens:

*   **Configurações Declarativas (Pydantic / `app/core/config.py`)**: O Pydantic já é exaustivamente testado em sua própria base, e os ambientes em `BaseSettings` sofrem inferência da lib. Erros no `.env` interrompem a aplicação em deploy, validando a si mesmos sem necessidade de mocks custosos num teste.
*   **Modelos Numéricos do SQLAlchemy Puros (`app/models/`)**: Suas definições (tamanhos de varchar ou chaves estrangeiras) já ganham verificação grátis via SQLAlchemy e Alembic no momento do init.
*   **Schemas Pydantic sem Validadores (Classes Básicas)**: As próprias validações de tipagem e formato (`BaseModel`, propriedades obrigatórias) também nascem perfeitamente testadas vindas do próprio FastAPI e seriam redundantes. A exceção aplica-se aos blocos de `@model_validator`, que já englobamos naturalmentes ao testarmos com o `TestClient` (E2E).
*   **Arquivos de Setup (ex: `app/db/init_db.py`, `app/main.py`)**: A mecânica de inicialização do FastAPI, CORS, attachs de Middlewares não carregam logica de negócio variante. A própria geração do `TestClient` atesta a sanidade do `main.py` de fora para dentro.

---

## 4. Máxima Porcentagem de Cobertura Possível (Alvo Recomendado)

Vislumbrando o cenário arquitetônico atual:

> A **meta realista ideal e altamente profissional deve orbitar entre 85% e 90%** global.

**Por quê não mirar em 100%?** 
Chegar a 100% frequentemente envolve manobras exdrúxulas (mockar bibliotecas de terceiro intensamente, injetar contextos absurdos só para invocar um `Exception` residual em um utilitário, ou testar injetores `Depends(...)` nativos do próprio FastAPI). Isso eleva drasticamente a manutenção mecânica e instaura as famigeradas **Vanity Metrics** (métricas de vaidade). 

Uma cobertura entre **85-90%** focada rigorosamente nos *Services*, *Segurança* e *Utilitários* é o ponto ouro para um projeto de larga duração sem comprometer o "time-to-market" das novas features — visto que cobre os "caminhos felizes" e quase todas as exceções (edge cases e fluxos de erro).

---
## Resumo do Caminho Crítico

Se quisermos evoluir rapidamente essa saúde arquitetural para o prêmio:

1. Subir a cobertura da `app/services/roles_service.py` e `app/services/user_roles_service.py`.
2. Encadear os testes puros dos validadores de e-mail e CPFs/CNPJs do utilitário (`test_validators.py`).
3. Construir um E2E básico de Auth para verificação da lib JWT (Garante segurança e levanta a métrica do `auth.py`).
