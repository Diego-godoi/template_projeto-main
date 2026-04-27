# Análise de Arquitetura e Padrões de Projeto

Este documento detalha os padrões arquiteturais e de design (*Design Patterns*) implementados no backend do projeto, focando em manutenibilidade, segurança e separação de preocupações.

## 1. Arquitetura Geral

O projeto adota uma arquitetura em camadas estruturada sobre o framework **FastAPI**, utilizando **PostgreSQL** com **SQLAlchemy** para persistência e **Alembic** para versionamento de banco de dados.

A estrutura é dividida em camadas horizontais desacopladas:
- **Controllers (Rotas)**: Localizados em `app/api/endpoints/`, gerenciam o ciclo de vida das requisições HTTP, roteamento e injeção de dependências.
- **Service Layer (Camada de Serviço)**: Localizada em `app/services/`, concentra toda a lógica de negócios e orquestra a persistência de dados.
- **Modelos (Entities / DB)**: Em `app/models/`, representam apenas o esquema do banco de dados e o estado dos objetos, sem lógica de persistência embutida.
- **Schemas (DTOs)**: Em `app/schema/`, utilizam Pydantic para validação, serialização e definição de contratos de interface.

---

## 2. Padrões de Projeto (Design Patterns)

### 2.1. Data Mapper
Diferente do padrão *Active Record*, onde o modelo conhece o banco de dados, aqui utilizamos o **Data Mapper**. Os modelos em `app/models/` são objetos passivos. A lógica de persistência (operações de CRUD e consultas complexas) reside inteiramente na **Service Layer**. Isso permite que o domínio da aplicação seja testado e evoluído sem dependência direta do estado do banco.

### 2.2. Dependency Injection (Injeção de Dependência)
Utilizado extensivamente através do sistema `Depends()` do FastAPI. É a base para a gestão de segurança (tokens JWT), injeção de serviços nos controllers e fornecimento da sessão do banco de dados (`Session`).

### 2.3. Unit of Work (Sessão Transacional)
A sessão do SQLAlchemy é injetada no início da requisição e repassada às camadas de serviço. Isso garante a atomicidade das transações: múltiplas operações de banco dentro de um único serviço podem ser confirmadas (*commit*) ou revertidas (*rollback*) em conjunto.

### 2.4. Data Transfer Object (DTO)
Implementado via modelos Pydantic. Eles garantem que os dados que circulam entre o cliente e o servidor sejam validados e filtrados, evitando a exposição acidental de atributos internos das entidades de banco de dados.

---

## 3. Diretrizes de Estrutura e Segurança

### 3.1. Tratamento de Exceções e Desacoplamento
Para manter a pureza da arquitetura, as camadas de Serviço e Banco não possuem conhecimento sobre o protocolo HTTP.
- **Fluxo:** Caso ocorra um erro (ex: entidade não encontrada), a camada inferior lança uma exceção de domínio (ex: `EntityNotFound`).
- **Handler:** O FastAPI captura essas exceções através de um `exception_handler` global em `app/main.py`, convertendo-as no status HTTP adequado (404, 422, etc.).

### 3.2. Isolamento de Efeitos Colaterais
Operações de infraestrutura que não pertencem ao banco de dados, como manipulação de arquivos no sistema operacional ou integração com APIs externas, são delegadas exclusivamente aos **Serviços**. A camada de modelos permanece livre de I/O de arquivos.

### 3.3. Segurança e Performance
- **Rate Limiting (Throttling):** Proteção contra ataques de força bruta em endpoints críticos via `slowapi`.
- **Sanitização de Consultas:** Validação rigorosa de inputs em operadores de busca (como `ILIKE`) para evitar sobrecarga de processamento no PostgreSQL e prevenir vulnerabilidades de negação de serviço (DoS) na camada de dados.
- **Modularidade Vertical:** Recomendação de transição para *Vertical Slicing* em módulos de alta complexidade, agrupando `router`, `service` e `model` por domínio de negócio para facilitar a escalabilidade.

---

### 4. Pilha Tecnológica Principal
* **Framework:** FastAPI
* **ORM:** SQLAlchemy 2.0 (Estilo Data Mapper)
* **Database:** PostgreSQL
* **Validation:** Pydantic V2
* **Migrations:** Alembic
* **Testing:** Pytest com instâncias transacionais isoladas