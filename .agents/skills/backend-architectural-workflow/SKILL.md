---
name: backend-architectural-workflow
description: O roteiro de etapas sequencial obrigatório para a construção de novas features completas na API do projeto. Use ao planejar a criação de uma entidade do zero.
---

# Fluxo Organizacional e Arquitetural (FastAPI)

Se a requisição envolver criar ou refatorar profundamente um fluxo estruturado do zero, você **DEVE rodar esse workflow ordenadamente e de baixo para cima**. Jamais codifique rotas antes das regras de banco de dados se solidificarem.

A sequência deve ser rigorosamente estipulada em:

## Passo-a-Passo de Implementação:

1. **Topologia / Models** 
   - Idealização da estrutura abstrata em classes ORM SQLAlchemy, refletindo a base lógica de Foreign Keys e regras de banco.
   
2. **Setup do DB (Alembic)**
   - Validação da compatibilidade das tabelas no `env.py` e subsequente geração e auditoria dos scripts de Migration do Alembic (assegurando `upgrade` e `downgrade` reversíveis).

3. **Data Transfer / DTO (Schemas)**
   - Configuração de assinaturas e validação via BaseModel do Pydantic, garantindo obrigatoriamente tipagem `[Request]` explícita e `[Response]` padronizada.

4. **Lógica de Business e Facade (Services)**
   - Desenho de abstrações autônomas na pasta `/services`. As chamadas recebem parâmetros injetados do DB para resolverem restrições sistêmicas puras (isoladas da request assíncrona HTTP em si).

5. **Acesso Final e Distribuição (Endpoints)**
   - Escrita dos controladores FastAPI/Routes (e.g., `/api/endpoints/xyz`) estritamente visando coletar e empacotar a viação de comunicação (Depends auth, injetar DB get_db) redirecionando as execuções e serializações para a Camada (4).
