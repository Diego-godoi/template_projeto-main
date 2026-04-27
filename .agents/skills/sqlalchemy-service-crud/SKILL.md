---
name: sqlalchemy-service-crud
description: Padronização de operações de banco de dados assíncronas utilizando session.execute() diretamente na camada de Serviço.
---

# Operações de Banco de Dados nos Services

Neste projeto, a camada de **Service** é a responsável direta pela execução das queries via `AsyncSession`, sem o uso de padrões intermediários como Repository.

## Diretrizes de Implementação

- **Uso do SQLAlchemy 2.0:** Utilize a sintaxe moderna de estilo 2.0. Exemplo: `select(Model).where(...)` em vez de `db.query(Model)`.
- **Execução Assíncrona:** Toda interação com o banco deve ser feita através de `await db.execute(statement)`.
- **Tratamento de Resultados:**
    - Para retornar um único objeto: `result.scalars().first()`.
    - Para retornar uma lista: `result.scalars().all()`.
- **Injeção de Dependência:** A `db: AsyncSession` deve ser sempre injetada via parâmetro nas funções do serviço, vinda do `Depends(get_db)` do endpoint.
- **Transacionalidade:** O `await db.commit()` e `await db.rollback()` devem ser gerenciados dentro do serviço, garantindo que operações que envolvam múltiplas tabelas sejam atômicas.

## Exemplo Padronizado
```python
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()
```