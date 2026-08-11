---
name: sqlalchemy-service-crud
description: Padronização de operações de banco de dados assíncronas utilizando session.execute() diretamente na camada de Serviço.
---
# Operações de Banco de Dados nos Services

Neste projeto, a camada de **Service** é a responsável direta pela execução das queries via `AsyncSession`, sem o uso de padrões intermediários como Repository.

## Diretrizes de Implementação

* **Uso do SQLAlchemy 2.0:** Utilize a sintaxe moderna de estilo 2.0. Exemplo: `select(Model).where(...)` em vez de `db.query(Model)`.
* **Execução Assíncrona:** Toda interação com o banco deve ser feita através de `await db.execute(statement)`.
* **Tratamento de Resultados:**
* Para retornar um único objeto: `result.scalars().first()`.
* Para retornar uma lista: `result.scalars().all()`.
* **Injeção de Dependência:** A `db: AsyncSession` deve ser sempre injetada via parâmetro nas funções do serviço, vinda do `Depends(get_db)` do endpoint.
* **Transacionalidade:** O `await db.commit()` e `await db.rollback()` devem ser gerenciados dentro do serviço, garantindo que operações que envolvam múltiplas tabelas sejam atômicas.
* **Prevenção de Race Conditions:** Em operações com potencial de acessos concorrentes ao mesmo registro (ex: atualização de estoques, saldos, reservas ou alteração de status por múltiplos processos), **é obrigatória a utilização de mecanismos de Lock**. O controle de concorrência garante a integridade dos dados, evitando que escritas simultâneas causem perda de atualizações (*lost updates*) ou leituras inconsistentes.

## Exemplos Padronizados

**Consulta Simples (Leitura)**

```python
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()

```

**Operação com Proteção de Concorrência (Lock)**

```python
async def transferir_saldo(
    db: AsyncSession, 
    conta_origem_id: int, 
    conta_destino_id: int, 
    valor: float
) -> None:
    # Ordenação dos IDs para evitar deadlocks em múltiplos registros
    id_primeiro, id_segundo = sorted([conta_origem_id, conta_destino_id])

    # Consulta com aplicação de Lock para evitar race condition
    query = (
        select(Conta)
        .where(Conta.id.in_([id_primeiro, id_segundo]))
        .with_for_update()
    )
    result = await db.execute(query)
    contas = {conta.id: conta for conta in result.scalars().all()}

    conta_origem = contas.get(conta_origem_id)
    conta_destino = contas.get(conta_destino_id)

    if not conta_origem or not conta_destino:
        raise ContaNaoEncontradaError("Uma ou ambas as contas não foram encontradas.")

    if conta_origem.saldo < valor:
        raise SaldoInsuficienteError("Saldo insuficiente para a operação.")

    # Atualização dos dados e persistência
    conta_origem.saldo -= valor
    conta_destino.saldo += valor

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

```