# Comandos

Para facilitar o utilizaçao de comandos de terminal utilizamos [taskpy](https://github.com/abhinavsingh/task.py), diminuindo a verbosidade dos camandos mais utilizados neste projeto.

---

- Roda o a API com auto reload `true`, expondo-a na rede com a porta:7000.

```bash
#uvicorn app:app --reload --host 0.0.0.0 --port 7000 --proxy-headers --forwarded-allow-ips
task run
```

---

- Verifica o padrao de codigo utilizano formatador de código [blak](https://github.com/psf/black) e organiza os imports com [isort](https://pycqa.github.io/isort/).

```bash
#black --check --diff . && isort --check --diff .
task lint
```

---

- Roda o servidor de documentaçao [mkdocs](https://www.mkdocs.org/)

```bash
#mkdocs serve -v
task docs
```

---

- Executa testes no codigo utilizando [pytest](https://docs.pytest.org/en/latest/), se for bem sucedido executa o [coverage](https://coverage.readthedocs.io/en/latest/) `task post_test`

```bash
#pytest -s -x --cov=app -vv
task test
```

---

- Exibe o resultado do coverage no navegador 'google-chrome' , caso deseje alterar o navegador, modifique o comando em `./pyproject.toml`

```bash
#google-chrome htmlcov/index.html
task cov
```

---

- Cria um `autogenerate` migrate dos models com [alembic](https://alembic.sqlalchemy.org/en/latest/)

```bash
#read -p 'nome da revision: ' nome && alembic revision --autogenerate -m $nome
task rev
```

---

- Aplica a ultima revisão ao banco de dados utilizando [alembic](https://alembic.sqlalchemy.org/en/latest/)

```bash
#alembic upgrade head
task up
```

---

- Desfaz todas as revisoes do banco utilizando [alembic](https://alembic.sqlalchemy.org/en/latest/)

```bash
#alembic downgrade base
task down
```

---

- Cria o arquivo de dependcias `requirements.txt`  utilizando [poetry](https://python-poetry.org/docs/cli/#export)

```bash
#poetry export > requirements.txt --without-hashes
task export
```

---

- Instala exatamente Dependecias contida em `requirements.txt`  utilizando [poetry](https://python-poetry.org/docs/cli/#install)

```bash
#cat requirements.txt | grep -E '^[^# ]' | cut -d ';' -f1  | xargs -n 1 poetry add
task install_req
```

---

- Instala a ultima versão das Dependecias contida em `requirements.txt`  utilizando [poetry](https://python-poetry.org/docs/cli/#install)

```bash
#cat requirements.txt | grep -E '^[^# ]' | cut -d '=' -f1  | xargs -n 1 poetry add
task install_up_req
```

---

- Verifica se são satisfeitas todas as comdições de `.pre-commit-config.yaml`  utilizando  [pre-commit](https://pre-commit.com/)

```bash
#pre-commit run --all-files
task pc
```

---

- Verifica se são satisfeitas todas as comdições de `.pre-commit-config.yaml` e atualiza os pacotes, utilizando  [pre-commit autoupdate](https://pre-commit.com/#updating-hooks-automatically)

```bash
#pre-commit autoupdate
task pc_update
```

---

- Inicia o container [docker](https://docs.docker.com/) onde se encontra o banco de dados, obs: deve ser utilizado em um container valido

```bash
#docker start postgres
task init_db
```

---
