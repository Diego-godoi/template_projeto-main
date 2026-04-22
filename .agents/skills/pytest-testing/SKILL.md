---
name: pytest-testing
description: Diretrizes para criar e revisar testes pytest, com foco em async e boas práticas.
---

# Skill de Teste com Pytest

Ao escrever ou revisar testes usando `pytest`, siga estas diretrizes para garantir confiabilidade, legibilidade e manutenibilidade.

## Checklist de Revisão

1.  **Corretude**: O teste verifica o comportamento pretendido?
2.  **Tratamento Async**: Funções assíncronas são testadas com `pytest-asyncio`? Garanta que `@pytest.mark.asyncio` ou `async def` sejam usados corretamente.
3.  **Isolamento**: Os testes limpam o ambiente após a execução? (ex: rollback de banco de dados).
4.  **Casos de Borda**: Condições de limite e erros são testados?
5.  **Legibilidade**: Os nomes dos testes são descritivos e auto-explicativos?

## Boas Práticas

### 1. Convenções de Nomenclatura
-   **Arquivos**: `test_*.py` ou `*_test.py`
-   **Funções**: `test_*`. **REGRA IMPORTANTE**: O nome da função deve ser auto-explicativo.
    -   Exemplo Ruim: `test_cpf`
    -   Exemplo Bom: `test_verifica_cpf_invalido`, `test_cria_usuario_com_sucesso`
-   **Classes**: `Test*`

### 2. Uso de Fixtures
-   Use `conftest.py` para fixtures compartilhadas.
-   Prefira fixtures a funções auxiliares para setup/teardown.
-   Use fixtures com `yield` para limpeza.

```python
import pytest

@pytest.fixture
def dados_exemplo():
    data = {"chave": "valor"}
    yield data
    # limpeza após o yield
```

### 3. Parametrização
-   Use `@pytest.mark.parametrize` para testar múltiplas entradas com a mesma lógica.

```python
import pytest

@pytest.mark.parametrize("entrada,esperado", [
    (1, 2),
    (2, 3),
])
def test_incremento(entrada, esperado):
    assert entrada + 1 == esperado
```

### 4. Testes Assíncronos
-   Como este projeto usa `pytest-asyncio`, defina testes assíncronos como `async def test_...`.
-   Use fixtures `async` se o setup exigir operações assíncronas.

```python
import pytest

@pytest.mark.asyncio
async def test_funcao_assincrona():
    resultado = await alguma_funcao_assincrona()
    assert resultado == valor_esperado
```

### 5. Interação com Banco de Dados
-   Garanta que testes usando o banco rodem em uma transação que sofra rollback.
-   Use factories ou fixtures do `sqlalchemy` para criar dados de teste.

## Como Fornecer Feedback
-   **Seja Específico**: aponte linhas ou blocos específicos.
-   **Explique o Porquê**: "Use uma fixture aqui para evitar duplicação de código no setup".
-   **Sugira Código**: Forneça um trecho de como o teste deve ficar.
