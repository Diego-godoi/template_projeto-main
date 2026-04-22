# Workflow Standard para Desenvolvimento de Projetos Backend (FastAPI + SQLAlchemy)

Este documento estabelece o processo padronizado de ciclo de vida e engenharia de software para o desenvolvimento de novos projetos backend. Seu objetivo principal atua como diretriz arquitetural para a equipe e como contexto fundamental de *System Prompt* na automação gerada por Inteligência Artificial (ex: Antigravity Skills), garantindo uniformidade, consistência qualitativa e previsibilidade no código gerado.

---

## 1. Planejamento e Especificação

A fundamentação analítica é o primeiro passo para garantir um desenvolvimento assertivo. Não se escreve código sem um direcionamento estruturado.

1. **Levantamento e Refinamento Inicial:**
   - Elaborar as especificações funcionais e a delimitação das regras de negócio.
   - Esclarecer os casos de uso críticos antes da idealização da infraestrutura.
2. **Documentação e Acompanhamento Diferenciado:**
   - Criar e gerenciar artefatos Markdown (`.md`) para divisão de épicos em tarefas granulares.
   - Manter um *checklist* sequencial (Ex: `[ ] Elaboração do Model Cliente -> [ ] Criação do Serviço Cliente -> [ ] Configuração de Endpoints e Testes`).
3. **Contextualização Sintética para IAs:**
   - O refinamento dos documentos gerará artefatos de otimização de prompt (*System Contexts*).
   - O objetivo é introduzir a IA no projeto com um mapa funcional previamente mastigado, reduzindo "alucinações" e alinhando-a às restrições estritas do framework subjacente.

---

## 2. Tecnologias Principais

Para assegurar compatibilidade, todas as automações devem respeitar o seguinte *stack* fixo:
- **Framework Web:** `FastAPI`
- **ORM e Banco de Dados:** `SQLAlchemy` nativo sobre `PostgreSQL` (Sem dialetos customizados ou extensões atípicas salvo caso de uso expresso, ex. GIS).
- **Contratos e Validação:** `Pydantic` (Validação I/O).
- **Versionamento de Banco:** `Alembic`
- **Validação de Testes:** `pytest` (Priorizando fixtures isoladas).

---

## 3. Arquitetura Base e Organização de Diretórios

Em cenários onde um template repositório não estiver disponível, o *scaffolding* do projeto deve aderir severamente à arquitetura descrita abaixo. A estrutura emprega os princípios de *Clean Architecture* somados a um padrão MVC simplificado, impondo a rigorosa separação de responsabilidades intrínsecas ao processo de escalonamento.

```text
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/    (Controladores FastAPI responsáveis estritamente pelo roteamento HTTP e injeção de dependências)
│   │   └── services/     (Camada de abstração central contendo lógica de domínio e transações do SQLAlchemy)
│   ├── auth/             (Módulos voltados para segurança, geração de JWT e políticas de acesso)
│   ├── core/             (Sistemas de configuração ambiental, parsing de .env e constantes fixas)
│   ├── db/               (Instâncias do Engine, declarações da Base Declarative e gestão de Sessões)
│   ├── error/            (Manipuladores de HTTPExceptions interceptáveis customizados)
│   ├── models/           (Mapeamento Objeto-Relacional referenciando a topologia SQL)
│   ├── schema/           (Esquemas Pydantic estabelecendo os contratos JSON estritos da API)
│   └── util/             (Módulos puramente funcionais, dissociados de estado: I/O arquivos, conversões, etc.)
├── alembic/              (Artefatos do ciclo de vida das migrações do banco de dados)
├── tests/                (Catálogo de cobertura unitária e de integração, incluindo conftest.py)
├── pyproject.toml        (Mapeamento oficial do ecossistema de dependências atreladas ao projeto)
└── requirements.txt      (Representação determinística das bibliotecas fixadas)
```

**Diretrizes do Desacoplamento:**
- **Roteadores (Endpoints):** São simplificados e delegadores. Devem limitar-se a gerir parâmetros, extrair credenciais (`Depends`) e retornar serializações padronizadas sem misturar regras SQL.
- **Camada de Serviço (Services):** Absorve a complexidade. Operações relacionais, cálculos iterativos e consolidação de chamadas a APIs terciárias pertencem exclusivamente aos métodos desta camada.
- **Dualidade de Tipos (Schema x Model):** Transito externo é regido rigorosamente pelo Pydantic (`schema/`). O encapsulamento em banco de dados responde apenas pelas restrições de integridade do SQLAlchemy (`models/`).

---

## 4. Fluxo Orientado a Desenvolvimento

Para garantir estabilidade, o desenvolvimento caminha através de uma técnica iterativa de validação: Da base de dados até ao acesso público.

1. **Desenvolvimento Estruturado (Models):**
   - Idealização das entidades `SQLAlchemy`.
   - Mapeamento estrito de chaves estrangeiras, relações e restrições.
2. **Evolução de Estado do Banco (Migrações Automáticas):**
   - Transição e geração das migrações utilizando a abstração do `Alembic`.
3. **Estabelecimento de Contratos (Schemas):**
   - Codificação dos protocolos `Request` (Validação de entrada) e `Response` (Apresentação de saída com `data` e `meta`) padronizados.
4. **Resolução Lógica (Services):**
   - Implementação das regras estabelecendo ligações via injeção de dependência na manipulação da sessão do DB.
5. **Acesso e Distribuição (Endpoints):**
   - Conclusão da rota submetendo o uso ao consumidor final.

---

## 5. Gatilhos Arquiteturais Complementares para IAs

Especificações inegociáveis ao gerar novo código para a *codebase*:
- **Padronização de Retorno (Pydantic):** Para todas as listagens ou buscas paginadas, deve-se criar uma classe correspondente contendo estritamente as chaves `meta: MetaData` e `data: list[Schema]`. Nunca inventar novas estruturas arbitrárias como `items` ou `results` dentro da representação.
- **Herança e Reuso Base:** Tabelas no framework atual descendem de uma classe utilitária de banco de dados (`app/db/base_class.py`) que já abstrai requisições genéricas transversais como CRUD. A IA tem a obrigação de invocar esses manipuladores (`query_params()`, `get()`) na camada Service, evadindo duplicação de instruções genéricas `select()`.
- **Tratativas de Exceções:** Evitar a invocação nativa solta da classe `HTTPException`. Fazer uso do controlador central, como por exemplo os métodos criados na arquitetura diretorial interna (`app.error`).
- **Engenharia de Qualidade:** Procedimentos Pytest desenvolvidos não emularão integrações persistentes diretamente do zero. Eles são acoplados pelo design providenciado pelo `conftest.py` com *mocks* provisórios para simular injeções em rotas.
- **Tratamento de Arquivos (`UploadFile`):**
  - **Uso Correto em Formulários:** Para permitir requisições `multipart/form-data` nos *schemas* Pydantic (`.as_form`), campos de imagem ou vídeo opcionais devem ser declarados com `UploadFile | None = File(None)`.
  - **Prevenção de `NoneType` em Services:** Nunca armazene ou processe campos de arquivo cegamente no método *patch* ou *create*. O FastAPI passa o valor `None` quando o arquivo é opcional e não foi enviado. 
  - **Exemplo de Verificação Segura (Patching):**
    ```python
    for key, value in update_data.items():
        if key == "image":
            # 🚨 CRÍTICO: Valide antes de chamar util.save_file()
            if value is not None and hasattr(value, "size") and value.size > 0:
                image_to_delete = entity.image_url
                image_name = util.save_file(value, "image")
                setattr(entity, "image_url", image_name)
    ```
