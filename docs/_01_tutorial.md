# Tutorial

## Requisitos

Esta aplicação uiliza Python 3.10 ou superior, suas dependecias estão divididas em:

---

- **Requisitos da API**:

```txt
python = "^3.11"
fastapi = "^0.93.0"
sqlalchemy = "^2.0.5.post1"
uvicorn = "^0.20.0"
python-magic = "^0.4.27"
pyjwt = "^2.6.0"
pydantic = {extras = ["email"], version = "^1.10.6"}
python-dotenv = "^1.0.0"
python-multipart = "^0.0.6"
jinja2 = "^3.1.2"
bcrypt = "^4.0.1"
email-validator = "^1.3.1"
psycopg2-binary = "^2.9.5"
alembic = "^1.10.2"
```

---

- **Requisitos da Documentaçao**:

```txt
mkdocs-material = "^9.1.2"
mkdocstrings = "^0.20.0"
mkdocstrings-python = "^0.8.3"
mkdocs-swagger-ui-tag = "^0.6.1"
mkdocs-macros-plugin = "^0.7.0"
jinja2 = "^3.1.2"
pymdown-extensions = "^9.10"
```

---

- **Requisitos de desenvolvimento**

```txt
isort = "^5.12.0"
black = "^23.1.0"
taskipy = "^1.10.3"
pre-commit = "^3.1.1"
```

---

- **Requisitos de testes**

```txt
pytest-asyncio = "^0.21.0"
sqlalchemy-utils = "^0.40.0"
faker = "^18.3.1"
pytest = "^7.2.2"
pytest-cov = "^4.0.0"
httpx = "^0.23.3"
```

---

## Instalação

Recomendamos o uso do `poetry`.

- Poetry é uma ferramenta para gerenciamento de dependência e empacotamento em Python. Ele permite que você declare as bibliotecas das quais seu projeto depende e as gerenciará (instalará/atualizará) para você. mais informaçoes consulte [poetry.org](https://python-poetry.org/docs/)

---

### [Poetry](https://python-poetry.org/docs/cli/#install)

- instalar dependencias.

```console
poetry install
```

---

### [python venv](https://docs.python.org/3/library/venv.html#module-venv)

- Criar ambiente

```console
python -m venv /path/to/new/virtual/environment
```

- Ativar ambiente.

```console
source /path/to/new/virtual/environment/bin/activate
```

- Instalar dependencias.

```console
pip install - r requirements.txt
```

---
