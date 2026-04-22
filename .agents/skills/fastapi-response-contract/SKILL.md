---
name: fastapi-response-contract
description: Padrão inegociável de formatação de respostas Pydantic para endpoints de listagem. Use sempre que for criar saídas paginadas na API.
---

# Contratos de Resposta Paginada

Para manter o contrato com o Frontend previsível e consistente, listagens não podem vazar a estrutura interna do banco.

Para todas as listagens (paginadas ou não), a classe correspondente de Resposta deve conter ESTRITAMENTE as chaves root:
- `meta: MetaData` (contendo dados de paginação, skip, limit, contagens totais)
- `data: list[EsquemaInterno]` (contendo propriamente a lista de itens)

**PROIBIDO:** 
- Inventar novas estruturas arbitrárias no json root da resposta.
- Criar chaves soltas como `items`, `results` ou `objects` dentro das respostas.
- Retornar listas diretas do SQLAlchemy sem passá-las por `ResponseModel(data=..., meta=...)`.
