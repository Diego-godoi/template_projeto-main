---
name: tdd-backend-workflow
description: Workflow interativo de TDD (Red-Green-Refactor) que conecta e aplica as diretrizes das skills `pytest-testing` e `sqlalchemy-service-crud`.
---

# Skill: Desenvolvimento Guiado por Testes (TDD Workflow)

Esta skill orquestra o ciclo de desenvolvimento backend utilizando **Test-Driven Development (TDD)** em 3 etapas estritas. Ela garante cobertura total, design orientado a testes e alinhamento completo com os padrões do projeto.

---

## 🔗 Referências de Arquitetura

Esta skill estende e consome diretamente as regras definidas em:
* **`pytest-testing`**: Para estrutura de arquivos, padrão AAA, parametrização, distinção entre `build()` e `create()` e checklist de qualidade.
* **`sqlalchemy-service-crud`**: Para sintaxe SQLAlchemy 2.0 assíncrona, gestão de transações e assinaturas da camada Service.

---

## 🔄 O Ciclo TDD (Fluxo de Execução Interativo)

Quando o usuário solicitar o desenvolvimento de uma funcionalidade, **NÃO gere a solução completa de uma vez**. Siga rigorosamente as 3 fases abaixo.

---

### Fase 1: RED (Criar os Testes)

Com base nas regras de negócio e validações enviadas pelo usuário, escreva **APENAS** a suíte de testes.

1. **Testes Unitários (`tests/unit/`)**:
   * Foco em validações puras, regras de domínio e funções independentes.
   * Utilize `factory.build()` da skill `pytest-testing` (sem persistência).
   * Abuse de `@pytest.mark.parametrize` para cobrir caminhos felizes e tristes/casos de borda.

2. **Testes de Integração (`tests/integration/`)**:
   * Foco em operações de banco e fluxos completos do Service.
   * Utilize `factory.create()` para objetos persitidos.
   * Garanta o uso de `AsyncSession` e marcadores assíncronos.

⛔ **PARADA OBRIGATÓRIA:** Finalize a resposta da Fase 1 sem gerar nenhum código da camada Service. Pergunte ao usuário:
> *"Os cenários de teste cobertos (unitários e integração) atendem a todas as suas regras de negócio ou deseja ajustar/adicionar algum cenário antes de implementarmos o código?"*

---

### Fase 2: GREEN (Escrever o Código Mínimo)

Após o usuário aprovar os testes da Fase 1, implemente a camada de **Service** (`app/services/`).

1. **Siga a Skill `sqlalchemy-service-crud`**:
   * Utilize a sintaxe SQLAlchemy 2.0 (`select`, `await db.execute`).
   * Receba `db: AsyncSession` por parâmetro.
   * Gerencie a transacionalidade (`commit`/`rollback`) no Service.
2. **Código Estritamente Necessário**:
   * Escreva **apenas** o código necessário para fazer os testes do Passo 1 passarem. Não adicione abstrações precoces ou cenários não testados.

⛔ **PARADA OBRIGATÓRIA:** Finalize a resposta mostrando a implementação da Service e forneça o comando de execução para o usuário validar:
```bash
poetry run pytest tests/path/to/test.py -v

```

Pergunte: *"Os testes passaram no seu ambiente? Podemos prosseguir para a etapa de Refatoração?"*

---

### Fase 3: REFACTOR (Análise de Qualidade e Limpeza)

Após a confirmação de que os testes estão passando (GREEN), analise criticamente tanto a suíte de testes quanto a Service criada.

1. **Revisão contra o Checklist da Skill `pytest-testing**`:
* **Dead Code**: Remover qualquer código inútil ou import solto.
* **Isolamento**: Garantir que nenhum teste unitário acessou o banco de dados.
* **Clean Code**: Melhorar nomes de variáveis, legibilidade do Service e reutilização de fixtures.
* **Desempenho**: Verificar se mocks/factories estão otimizados.


2. Apresente o código refatorado e finalizado.

---

## 📋 Modelo de Prompt de Entrada (Como acionar)

Para iniciar uma tarefa usando esta skill, forneça:

1. **Descrição da Funcionalidade**: (ex: Cadastro de Usuário).
2. **Entidades/Modelos envolvidos**: (ex: Modelo `User`).
3. **Regras de Negócio e Validações**: (ex: Email único, CPF válido, senha mínima de 8 caracteres).