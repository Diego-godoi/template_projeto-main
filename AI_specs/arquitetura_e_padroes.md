# Análise de Arquitetura e Padrões de Projeto

Este documento detalha os padrões arquiteturais e de design (Design Patterns) identificados no backend do projeto (FastAPI), juntamente com recomendações de melhorias estruturais, arquiteturais e de segurança.

## 1. Arquitetura Geral

O projeto adota uma arquitetura orientada a APIs RESTful construída sobre o framework **FastAPI**, com persistência relacional utilizando **PostgreSQL** via **SQLAlchemy** (ORM) e migrações geridas pelo **Alembic**.

O padrão arquitetural dominante é uma variação do **MVC (Model-View-Controller)** / **Client-Server Architecture**, estruturado em camadas horizontais:
- **Controllers (Rotas)**: Localizados em `app/api/endpoints/`, lidam puramente com o tráfego HTTP, roteamento e injeção de dependências.
- **Service Layer (Serviços)**: Localizados em `app/api/services/`, abrigam a lógica de negócios da aplicação.
- **Modelos (Entities / DB)**: Em `app/models/`, contém a representação do banco de dados relacional.
- **Schemas (DTOs)**: Em `app/schema/`, usam o Pydantic para a validação, filtragem e transição de dados estruturados e serialização de respostas.

## 2. Padrões de Projeto (Design Patterns) Identificados

- **Data Transfer Object (DTO)**: Amplamente empregado com os modelos Pydantic (`app/schema/`). Eles garantem que apenas dados válidos circulem pelas fronteiras da aplicação.
- **Active Record / Table Data Gateway**: A classe `Base` em `app/db/base_class.py` injeta métodos de CRUD extensos (`create`, `update`, `login`, `remove`) contendo a própria execução da query e gerenciamento de sessão transacional internamente, tornando todos os modelos derivados entidades "ativas".
- **Dependency Injection (Injeção de Dependência)**: Prática essencial trazida do ecossistema FastAPI (usando `Depends()`), usada extensivamente em checagem de regras em endpoints (via formulário de login, header de tokens, etc.).
- **Singleton Pattern**: Observado em `app/core/config.py`, ao se instanciar a classe `Settings` globalmente `settings = Settings()` fornecendo configuração única para toda a aplicação.
- **Service Layer / Facade**: Em `app/api/services/`, várias classes servem como fachada (Facade) para delegar requisições diretamente aos modelos (ex: `models.Users.query_params()`), ou abrigar lógicas combinadas (CRUD base).

## 3. Recomendações e Melhorias

### 3.1. Arquitetura e Desacoplamento (Prioridade Alta)

1. **Separação de Preocupações (Single Responsibility Principle)**:
   - A classe principal de ORM (`app/db/base_class.py`) possui referências diretas do domínio da Web: `raise custom_HTTPException(e)`. 
   - **Problema:** A camada de banco de dados é acoplada ao contexto HTTP (FastAPI).
   - **Solução:** Erros de banco de dados (ex: `SQLAlchemyError`, `IntegrityError`) devem gerar ou levantar exceções de Domínio/Banco (ex: `EntityNotFoundException`), que são então interceptadas pelo gerenciador de exceções (`app/main.py`) e traduzidas em status HTTP 404, 422, etc. A classe `Base` não deve importar ou conhecer nada sobre APIs.

2. **Gerenciamento de Sessão Transacional (Unit of Work)**:
   - Os métodos em `base_class.py` ativam e fecham instâncias locais com `_db = SessionLocal()`... `_db.close()`.
   - **Problema:** Fica difícil testar operações e fazer *rollbacks* eficientes caso um serviço precise alterar três entidades ao mesmo tempo. 
   - **Solução:** Utilizar o padrão de **Injeção de Sessão**, onde o Controller inicializa a sessão via `Depends(get_db)` e repassa para a camada de serviço. Isso facilita enormemente o uso da _skill_ de automação de testes com `pytest`.

3. **Efeitos Colaterais no Banco de Dados**:
   - O método `remove_data_and_files` lida especificamente com chamadas à biblioteca do sistema operacional para `.delete_file()`.
   - **Problema:** Excluir arquivos no HD é uma regra de negócio / infraestrutura que não deveria pertencer à base abstrata de banco de dados.
   - **Solução:** Delegar estas manipulações híbridas à camada de `Service`.

### 3.2. Organização de Código

1. **Mover Services (Camada Isolada)**:
   - O diretório de serviços encontra-se dentro de `app/api/services/`. Os serviços devem ser o "motor independente" do software. Se amanhã um robô agendado via Celery sem API HTTP precisar chamar um serviço, fazê-lo de dentro de API quebra o contexto conceitual.
   - Seria preferível ter `app/services/` como camada adjacente a `api/`, `models/` e `db/`.

2. **Dando o Próximo Passo: Vertical Slicing (Modularidade)**:
   - Para projetos em expansão, manter "todos os `routers` de todos as entidades em uma pasta", "todos os `models` em outra", pode gerar alta fricção de alteração e leitura ("Horizontal Slicing").
   - Recomendamos gradualmente adotar **Domain-Driven Folder Structures / Modularidade Vertical**. Ex: `app/users/` contendo `router.py`, `service.py`, `model.py` e `schema.py`. Isso facilita muito a escalabilidade da equipe.

### 3.3. Melhorias de Segurança

1. **Rate Limiting em Endpoints Críticos (Throttling)**:
   - Atualmente, não parece haver proteção nativa impeditiva de força bruta nas rotas `/login/access-token` ou `/forgot-my-password/`.
   - Recomenda-se integrar algo como o `slowapi` limitando e.g., 5-10 requisições por IP por minuto para estes fluxos especifícos.

2. **Exposição Cautelosa sobre Consultas Parciais / ILIKE**:
   - No `base_class.py`, temos `.ilike(f"%{val}%")`. Dependendo de como o usuário manda este `%val%`, ou se a tabela escalar, o banco pode passar a necessitar de um index de texto (Gist/Trigram search), do contrário pode sofrer `Slow Query / CPU Spike` por Full Table Scans. Cuidado para não deixar buscas abertas sobre colunas de texto contínuo ilimitado onde abusos possam enfileirar os processos (vulnerabilidade de DoS na camada do DB).

3. **Proteção Rigorosa dos Logs**:
   - Com o desacoplamento das exceções, garantir que rastros em logs dos erros HTTP advindos do `SQLAlchemy` jamais transpareçam a arquitetura da tabela no banco aos requisitantes.
