---
name: sqlalchemy-service-crud
description: Aproveitamento do utilitário genérico de banco de dados 'base_class.py' do repositório em camadas de Serviço.
---

# Uso do Base Class do DB

As tabelas no framework atual herdam da classe genérica `Base` (`app/db/base_class.py`), a qual já abstrai e encapsula todos os CRUD genéricos.

## Como proceder nos Services

- Na camada de Services, você **DEVE focar na regra de negócio e invocar as funções utilitárias da base_class.py**.
- Exemplos do que priorizar: usar `Model.query_params()` para buscas filtradas ou `Model.get()` para consultas rápidas.
- Isto minimiza a duplicação genérica de instruções soltas de banco como `select()` manual. Se a busca é trivial, o `base_class.py` já sabe resolver.
- Certifique-se também de inicializar e transitar a injeção via `Depends(get_db)` trazidas das rotas nas assinaturas das funções de Serviço, tratando rollbacks explicitamente quando o fluxo da lógica alterar múltiplas instâncias em sequência caso fira alguma restrição.
