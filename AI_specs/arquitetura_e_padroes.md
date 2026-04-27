# Análise de Arquitetura e Padrões de Projeto (V2)

Este documento detalha os padrões arquiteturais e de design identificados no backend, com foco em uma estrutura desacoplada, utilizando **Data Mapper** e uma camada de serviços robusta.

## 1. Arquitetura Geral

O projeto utiliza uma arquitetura baseada em camadas, focada no desacoplamento entre a persistência de dados e a lógica de negócios:

- **Controllers (Rotas)**: Localizados em `app/api/endpoints/`, gerenciam o protocolo HTTP e a injeção de dependências.
- **Service Layer (Camada de Serviço)**: Localizada em `app/services/`, é o motor da aplicação. Concentra a lógica de negócios e a orquestração da persistência (substituindo a lógica que antes ficava nos modelos).
- **Modelos (Entities)**: Em `app/models/`, representam apenas o estado e o mapeamento relacional, sem conter lógica de persistência ou conhecimento sobre a sessão do banco.
- **Schemas (DTOs)**: Em `app/schema/`, utilizam Pydantic para validação e contrato de interface.

## 2. Padrões de Projeto (Design Patterns) Identificados

- **Data Mapper**: Diferente do *Active Record*, os modelos não possuem métodos como `.save()` ou `.create()`. A responsabilidade de mapear e persistir os dados no banco de dados é transferida para a **Service Layer**, mantendo as entidades do domínio limpas.
- **Data Transfer Object (DTO)**: Uso de modelos Pydantic para garantir a integridade dos dados na entrada e saída da API.
- **Dependency Injection (Injeção de Dependência)**: Utilizada via FastAPI (`Depends()`) para injetar sessões de banco de dados e serviços nos endpoints, facilitando testes e inversão de controle.
- **Singleton Pattern**: Aplicado em `app/core/config.py` para centralizar as configurações da aplicação em uma única instância.
- **Unit of Work (Sessão Injetada)**: A sessão do banco de dados é gerida pelo ciclo de vida da requisição e injetada nos serviços, garantindo atomicidade nas transações.

## 3. Recomendações e Melhorias Implementadas

### 3.1. Desacoplamento e Persistência (Prioridade Alta)

1. **Migração para Data Mapper**:
   - **Mudança:** A lógica de CRUD foi removida da classe `Base` em `app/db/base_class.py` e movida para a camada de serviço.
   - **Benefício:** Os modelos tornam-se objetos simples (POPOs - *Plain Old Python Objects*), facilitando a manutenção e evitando que o modelo "saiba" como se salvar.

2. **Tratamento Global de Exceções**:
   - **Estratégia:** A camada de banco de dados e a camada de serviço não devem disparar `HTTPException`. Elas devem lançar exceções de domínio (ex: `UserNotFoundError`, `DatabaseIntegrityError`).
   - **Solução:** Utilizar o `exception_handler` do FastAPI em `app/main.py`. Isso centraliza a tradução de erros internos para códigos de status HTTP (404, 400, 500), mantendo o código das rotas e serviços limpo.

3. **Gerenciamento de Sessão Transacional**:
   - A sessão do SQLAlchemy (`db: Session`) é injetada diretamente no Controller e repassada ao Serviço. Isso permite que o Serviço execute múltiplas operações em uma única transação, facilitando o *rollback* em caso de falha.

### 3.2. Organização e Escalabilidade

1. **Serviços como Camada Independente**:
   - A pasta `services/` foi movida para a raiz (`app/services/`), tornando-a acessível não apenas por rotas HTTP, mas também por tarefas agendadas (Celery) ou scripts de CLI, sem dependência do contexto da API.

2. **Modularidade Vertical (Vertical Slicing)**:
   - Para novos módulos, recomenda-se a estrutura por domínio (ex: `app/modules/billing/`), agrupando rotas, serviços e modelos relacionados, reduzindo a carga cognitiva ao navegar no projeto.

### 3.3. Segurança e Performance

1. **Rate Limiting (Throttling)**:
   - Implementação de proteção contra força bruta em rotas sensíveis (Login/Recuperação de Senha) através de middlewares como `slowapi`.

2. **Otimização de Consultas (SQL Profiling)**:
   - Com a lógica de persistência centralizada nos serviços, torna-se mais fácil monitorar e otimizar buscas complexas (uso de `joinedload`, índices em colunas de busca `ILIKE`) para evitar gargalos de CPU no PostgreSQL.