---
name: fastapi-error-handling
description: Padrões arquiteturais para desacoplamento de exceções HTTP da camada de Banco de Dados.
---

# Políticas de Exceções e Erros HTTP

## 1. Separação de Preocupação
- A classe global de acesso ao DB (`base_class.py`) e transações puras NÃO DEVEM exportar nem chamar a lib do FastAPI relacionada a chamadas HTTP (como `HTTPException`).
- Acoplamento na camada de BD é antipadrão neste projeto. Erros de BD e `SQLAlchemyError` retornam instâncias customizadas ou vazam de maneira crua.
---
name: fastapi-file-handling
description: Diretrizes obrigatórias para recepção e manipulação de arquivos (UploadFile) em requisições de API no FastAPI. Use quando lidar com imagens, PDFs, multipart/form-data.
---

# Manipulação de Arquivos

## 1. No Schema
- Sempre use o parâmetro de formatação de Pydantic (`.as_form`) para lidar com formulários multipart.
- Campos de arquivo opcionais devem ser definidos explicitamente como opcionais: `UploadFile | None = File(None)`.

## 2. Nos Services
- **JAMAIS** armazene diretamente objetos que podem ser `NoneType` ou referências à memória em métodos de banco de dados (Patch/Update).
- O FastAPI passa o valor `None` quando o arquivo é opcional e não foi enviado no payload. Sempre verifique e valide.
- Exemplo de tratamento explícito obrigatório antes de salvar:
  ```python
  if value is not None and hasattr(value, "size") and value.size > 0:
      image_name = util.save_file(value, "image")
  ```

## 2. Centralização HTTP
- **Evite** invocar e codificar `raise HTTPException(status_code=...)` indiscriminadamente dentro do código solto em Services.
- **Transfira** o tratamento lógico via lançamento de exceções padronizadas mapeadas (`CustomException`, `EntityNotFoundException`) contidas preferencialmente em manipuladores como no diretório `app/error/`.
- O intuito destas camadas é traduzir exceções ríspidas de DB para códigos 400, 422 e 404 coerentes, protegendo informações críticas da topologia de tabelas (Traces de Integridade) que poderiam comprometer a segurança caso entregues em RAW no console do Frontend.
