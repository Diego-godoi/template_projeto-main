
# Estrutura do Diretório

---
Este documento descreve a organização e a finalidade de cada diretório e arquivo do projeto. A estrutura foi projetada seguindo as melhores práticas de desenvolvimento de APIs com FastAPI, promovendo modularidade, escalabilidade e facilidade de manutenção.A arquitetura do projeto separa claramente as responsabilidades: camadas de API, lógica de negócios, acesso a dados, autenticação, e recursos estáticos. Esta organização facilita a navegação no código, testes unitários e integração, além de permitir que novos desenvolvedores compreendam rapidamente a estrutura do sistema.Cada diretório possui um propósito específico, desde a definição de endpoints da API até a configuração de migrações de banco de dados. A documentação gerada automaticamente pelo MkDocs reflete essa estrutura, proporcionando uma visão clara e organizada de todos os componentes da aplicação.

---

## Arvore de diretorio

    backend
    ├── alembic
    │   └── versions
    ├── app
    │   ├── api
    │   │   └── v1
    │   │       └── endpoints
    │   ├── auth
    │   ├── core
    │   ├── database
    │   ├── db
    │   ├── models
    │   ├── schema
    │   ├── static
    │   │   ├── assets
    │   │   ├── css
    │   │   ├── img
    │   │   ├── js
    │   │   └── scss
    │   ├── templates
    │   ├── uploads
    │   └── util
    ├── docs
    │   ├── app
    │   │   ├── api
    │   │   │   ├── endpoints
    │   │   │   └── integration
    │   │   ├── auth
    │   │   ├── core
    │   │   ├── database
    │   │   ├── db
    │   │   ├── models
    │   │   ├── schemas
    │   │   ├── static
    │   │   │   ├── css
    │   │   │   ├── img
    │   │   │   ├── js
    │   │   │   └── scss
    │   │   ├── templates
    │   │   ├── uploads
    │   │   └── utils
    │   ├── assets
    │   └── stylesheets
    ├── htmlcov
    └── tests
        └── file_test

- **app**: Nível da aplicação, encapsula os módulos da aplicação `./backend/app/`
- **api**: Contém todos os endpoints do aplicativo `./backend/app/api/`
- **auth**:Se necessário, contém as regras de autenticação do aplicação, padrão de autorização baseado em OAuth 2.0 Permite que aplicativos como Web App, Mobile e Desktop obtenham acesso limitado às informações do usuário`./backend/app/auth/`.
- **core**: Contém todas as variáveis de ambiente usadas na aplicação `./backend/app/core/`, obtendo arquivos `.env` como fonte em `./`
- **database**: Se houver necessidade de pré-preencher os dados, eles devem ficar neste nível`./backend/app/database/`.
- **db**: Configuraçoes de conexão e construção do banco de dados `./backend/app/db/`.
- **models**: Deve conter todos os modelos do banco de dados. Modifique ou adicione modelos SQLAlchemy em `./backend/app/models/`
- **schema**: Responsável por validar a estrutura de dados antes de permitir a entrada em um endpoint.
- **static**: Somente se houver necessidade de elementos estáticos no projeto.
- **templates**: Se necessário, deve conter os templates do projeto.
- **uploads**: Se necessário, diretorio para salvar arquivos. sura `uri` pode ser alterada em `.env` contido em `./`.
- **util**: Módulo que contém métodos que podem ou não ser reutilizados em diferentes projetos.
- **docs**: Se existir, deve conter a documentação da aplicaçao `./backend/docs/`
- **tests**: O cenário ideal. Escreva seus testes. `./back-end/tests/`
- **.env**: Todas as variáveis de ambiente podem ser encontradas no diretório `./backand/`(o arquivo `.env`)
- **Dependências**: Todas as dependências podem ser encontradas no diretório `./backend` (o arquivo `pyproject.toml` e `requiriments.txt`)
