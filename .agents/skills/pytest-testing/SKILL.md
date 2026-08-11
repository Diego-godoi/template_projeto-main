---
name: pytest-testing
description: Diretrizes para criar e revisar testes pytest, com foco em async e boas práticas.
---

# Skill: Engenharia de Testes com Pytest

Esta skill define o padrão de alta performance para a suíte de testes. O foco é **eficiência, legibilidade e cobertura inteligente**, sem configurações globais fixas e focada em execução via CLI.

## 1. Arquitetura de Diretórios

A organização separa a **lógica de negócio** (Unit) da **lógica de sistema** (Integration).

```text
tests/
├── factories.py       # Ponto central para FactoryBoy
├── conftest.py        # Fixtures globais, db_session, clients
├── unit/              # Lógica pura, validadores, funções independentes
└── integration/       # Endpoints, DB, Auth, serviços acoplados

```

---

## 2. Estratégia de Dados com FactoryBoy

Utilize `factory_boy` como única fonte da verdade para dados de teste. A distinção entre **Unit** e **Integration** é feita pelo método de instanciamento:

* **Unitários:** Use `factory.build()`. Objeto em memória, sem acesso ao banco. Rápido e isolado.
* **Integração:** Use `factory.create()`. Persiste no banco de dados.

```python
# tests/factories.py
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = SessionLocal() # Injeção de sessão

    id = factory.Sequence(lambda n: n)
    username = factory.Faker("user_name")

```

---

## 3. Padrão de Codificação (AAA: Arrange, Act, Assert)

### A. Testes Unitários (Parametrização)

Foco em cobertura de casos de borda sem custo de performance.

```python
import pytest
from app.util.validators import validar_cpf

@pytest.mark.parametrize("cpf,esperado", [
    ("12345678909", True),
    ("00000000000", False),
    ("", False),
])
def test_validacao_cpf(cpf, esperado):
    # Arrange: Dado parametrizado
    # Act
    resultado = validar_cpf(cpf)
    # Assert
    assert resultado is esperado

```

### B. Testes de Integração (Async & DB)

Foco em comportamentos de sistema e rotas HTTP.

```python
import pytest
from tests.factories import UserFactory
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_atualizar_perfil_usuario(client: AsyncClient, db_session):
    # Arrange: Criação via DB
    user = UserFactory.create(username="diego_dev")
    payload = {"username": "diego_novo"}

    # Act: Requisição real
    response = await client.patch(f"/users/{user.id}", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["username"] == "diego_novo"

```

---

## 4. Gestão de Cobertura e Qualidade

Como não utilizamos `pytest.ini`, o controle de qualidade é feito via **CLI rigorosa**. Isso garante que qualquer desenvolvedor que rode os testes tenha o mesmo nível de exigência.

### Comando de Execução Padrão:

```bash
poetry run pytest tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-fail-under=85 \
    --asyncio-mode=auto

```

* `--cov=app`: Analisa apenas o código fonte.
* `--cov-report=term-missing`: Exibe no terminal exatamente qual linha ficou sem teste.
* `--cov-fail-under=85`: Build falha se a cobertura for inferior a 85%.
* `--asyncio-mode=auto`: Detecta automaticamente testes `async` sem precisar de decorators em todos os arquivos.

---

## 5. Checklist de Revisão (Regras de Ouro)

1. **Dead Code:** Se uma função não é usada, **delete-a**. Não crie testes para código que não deveria existir.
2. **Corretude**: O teste verifica o comportamento pretendido?
3. **Tratamento Async**: Funções assíncronas são testadas com `pytest-asyncio`? Garanta que `@pytest.mark.asyncio` ou `async def` sejam usados corretamente.
4. **Casos de Borda**: Condições de limite e erros são testados?
5. **Legibilidade**: Os nomes dos testes são descritivos e auto-explicativos?
6. **Isolamento:** Testes unitários não podem ter acesso ao `db_session`. Se precisar de banco, mova para `integration/`.
7. **Performance:** Testes unitários devem rodar em milissegundos. Se um teste demorar, verifique se há I/O indevido.
7. **Autodocumentação:** Se o teste falhar, a mensagem de erro (ou o nome do teste) deve dizer o que quebrou, sem precisar abrir o código.
8. **Cobertura**: A cobertura de testes é superior a 85%?


## Como Fornecer Feedback
- **Seja Específico**: aponte linhas ou blocos específicos.
- **Explique o Porquê**: "Use uma fixture aqui para evitar duplicação de código no setup".
- **Sugira Código**: Forneça um trecho de como o teste deve ficar.