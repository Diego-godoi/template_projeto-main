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
