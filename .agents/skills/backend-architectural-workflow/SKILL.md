---
name: backend-architectural-workflow
description: O roteiro de etapas sequencial obrigatório para a construção de novas features completas na API do projeto. Use ao planejar a criação de uma entidade do zero.
---

# Skill: Engenharia de Backend (MVC + Data Mapper)

Esta skill define o padrão arquitetural **MVC (Model-View-Controller)** para o backend, utilizando o padrão **Data Mapper** para persistência e **rejeitando explicitamente o Repository Pattern** para manter a camada de serviços enxuta e direta.

## 1. Fundamentos da Arquitetura

O projeto é estruturado para separar responsabilidades de forma estrita, focada em simplicidade e performance:

* **Models (Model):** Representam a estrutura de dados (ORM). São objetos puros (POPOs) de mapeamento relacional. Não possuem lógica de negócio ou de persistência (`.save()`, `.delete()`).
* **Schemas/DTOs (View):** Atuam como a "camada de visualização" da API. Utilizam Pydantic para garantir que o contrato de interface (JSON de entrada/saída) seja rigorosamente validado e serializado.
* **Controllers (Controller):** Localizados em `app/api/endpoints/`. Gerenciam o fluxo HTTP, extração de parâmetros e a resposta final ao cliente.

## 2. Padrão Data Mapper e a Camada de Serviço

A persistência de dados é tratada via **Data Mapper**, centralizando a responsabilidade na **Service Layer**.

* **Data Mapper:** A lógica de mapear os dados da entidade para o banco de dados (ou vice-versa) é delegada à camada de serviço. O modelo não "se conhece" no banco de dados.
* **Service Layer (O "Cérebro"):** É aqui que toda a lógica de negócio reside. O serviço recebe a `db: Session` (injeção de dependência), processa a lógica, manipula o modelo e persiste as mudanças diretamente via sessão do SQLAlchemy.

## 3. Diretriz Crítica: Omitir o Repository Pattern

**Regra de Ouro:** Não implemente uma camada de `repositories`.

* **Por que evitar:** Em nossa arquitetura MVC + Data Mapper, a introdução de *Repositories* adiciona uma camada de abstração desnecessária, causando *boilerplate* excessivo (classes de repositório apenas para delegar chamadas ao ORM).
* **Como fazer:** O serviço atua diretamente sobre os modelos e a sessão do banco. Se uma query é complexa, ela é escrita dentro do método de serviço que a utiliza. Isso mantém o fluxo de execução rastreável e reduz a carga cognitiva de navegar por múltiplos arquivos para entender uma simples operação de leitura/escrita.

## 4. Workflow Obrigatório de Implementação
Para garantir a integridade do sistema, novas funcionalidades devem seguir esta sequência estrita, de baixo para cima. Jamais codifique rotas antes das regras de banco estarem solidificadas.

* **Topologia (Models):** Defina a estrutura abstrata das entidades ORM. Mapeie relacionamentos, chaves estrangeiras e constraints.
* **Setup do Banco (Alembic):** Gere e audite os scripts de migração. Garanta que upgrade e downgrade sejam reversíveis e seguros.
* **Contratos (Schemas/DTOs):** Defina os Pydantic Models. Separe explicitamente os esquemas de Request (criação/atualização) e Response (leitura).
* **Lógica de Negócio (Services):** Implemente a lógica na camada de serviços. Receba o db: Session via injeção. Lance exceções de domínio (ex: UserNotFoundError), nunca HTTPException aqui.
* **Interface (Endpoints):** Escreva os controladores. Utilize Depends() para autenticação e sessão. Traduza exceções de domínio para HTTP (404, 400, etc.) no exception_handler global em app/main.py.

### 5. Padrões Técnicos e Implementação
* **Dependency Injection (DI):** Utilize FastAPI Depends() para injetar sessões e serviços.
* **Tratamento de Erros:** A camada de serviço não sabe que é uma API. Ela lança exceções de domínio que o exception_handler global traduz para status HTTP.
* **Unit of Work:** A sessão de banco de dados (Session) deve ser injetada e compartilhada durante todo o ciclo de vida da requisição para garantir atomicidade.
* **Modularidade (Vertical Slicing):** Agrupe funcionalidades por domínio (ex: app/modules/billing/) contendo suas próprias rotas, modelos e serviços sempre que possível.
* **Singleton:** Aplique para configurações globais em app/core/config.py.

---

## 5. Checklist de Arquitetura (Code Review)

* [ ] **MVC Respeitado:** O modelo contém lógica de persistência? Se sim, mova para o Service.
* [ ] **Repositórios:** Existe alguma pasta chamada `repository` ou classe terminando em `Repository`? **Delete-a** e mova a lógica para o Service.
* [ ] **Data Mapper:** A sessão (`db: Session`) está sendo usada corretamente na camada de serviço para persistir os modelos?
* [ ] **Desacoplamento:** O serviço está dependendo de `HTTPException` ou objetos de Request? Se sim, refatore para retornar exceções de domínio.
* [ ] **View (Schemas):** Todos os endpoints estão serializando a resposta via Pydantic Models (`response_model=...`)?

---

### Quando usar esta Skill?

* Sempre que for planejar a estrutura de um novo domínio (Vertical Slicing).
* Sempre que precisar refatorar um código que esteja "acidentalmente" seguindo padrões de *Active Record* (lógica dentro do modelo) ou *Repository* (abstração excessiva).
* Para manter a equipe alinhada na simplicidade: **Model (Estrutura) -> Service (Lógica) -> Controller (Entrada/Saída)**.