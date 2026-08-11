---
name: api-logging
description: O roteiro de implementação e revisão de logs no código fonte Python da API direcionados ao stdout para captura do Docker.
---

# Skill: Secure Python API Logging (Container-Friendly)

## 🎯 Objetivo
Analisar, gerar e refatorar implementações de log em APIs Python, garantindo observabilidade por mensagens naturais e legíveis via saída padrão (`stdout`), segurança de dados (No-PII) e delegação total do gerenciamento de persistência para o Docker.

## ⚙️ Regras e Restrições Técnicas
- **Zero Dependências Externas:** Utilize única e exclusivamente o módulo nativo `logging` do Python. É proibido o uso de `loguru`, `structlog` ou pacotes externos.
- **Níveis de Log Permitidos:**
  - `logger.info()`: Eventos de sucesso no fluxo de negócio, inicialização de serviços, início/fim de requisições e tarefas concluídas.
  - `logger.warning()`: Situações anômalas, mas contornáveis (ex: falhas de validação de input, 401/403, *rate limiting* atingido). **Nota:** Nunca use o método legado `.warn()`.
  - `logger.error()`: Falhas de infraestrutura (banco de dados, timeouts de rede) e exceções não tratadas. **Obrigatório** o uso de `exc_info=True` dentro de blocos `except`.
- **Privacidade e Segurança (Strict No-PII):**
  - É terminantemente proibido expor credenciais, senhas, hashes, tokens de sessão, JWTs ou chaves de API.
  - Informações Pessoais Identificáveis (PII) como e-mails, telefones ou documentos devem ser mascarados ativamente antes de disparar o log (ex: `u***@email.com`).
- **Formato de Mensagem Natural:** O formato final de saída deve ser uma linha de texto em linguagem natural e legível por humanos. A mensagem deve descrever claramente **o que aconteceu**, incluindo os dados relevantes de contexto (IDs, status, durações) embutidos na frase. Evite pares `chave='valor'` genéricos — prefira frases completas que façam sentido ao serem lidas diretamente no terminal ou em um agregador.
- **Filosofia Twelve-Factor App (Stream Logs):** A aplicação **nunca** deve gerenciar arquivos de log, diretórios locais ou rotação. Todos os logs devem ser tratados como um fluxo contínuo de eventos enviados diretamente para o terminal (`sys.stdout`), permitindo que o daemon do Docker capture e centralize os dados.

---

## ✅ Exemplos de Boas Práticas (Do)

### Configuração Inicial Nativa (Loggers para Terminal)
```python
import logging
import sys

# Criação do logger da aplicação
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Configuração do StreamHandler apontando explicitamente para a saída padrão
stream_handler = logging.StreamHandler(sys.stdout)

# Definição do formato em string simples: data [nível] mensagem
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
```

### INFO (Mensagens naturais de sucesso)

```python
# Descreva o que aconteceu, com os dados relevantes embutidos na frase
logger.info("Requisição GET /api/v1/resource concluída com status 200 em 45ms (request_id=%s)", req_id)
logger.info("Tarefa de envio de notificação iniciada para o usuário %d", user_id)
logger.info("E-mail enviado com sucesso para %s (notification_id=%s)", masked_email, notification_id)
logger.info("Serviço de pagamentos inicializado e pronto para receber requisições")
```

### WARNING (Anomalias contornáveis com contexto claro)

```python
logger.warning("Payload inválido em POST /api/v1/upload: arquivo excede o tamanho permitido (request_id=%s)", req_id)
logger.warning("Tentativa de autenticação falhou para %s — tentativa %d de 5", masked_email, attempts)
logger.warning("Rate limit atingido para o usuário %d, requisição bloqueada", user_id)
```

### ERROR (Falhas com captura de stack trace)

```python
try:
    process_transaction(data)
except ConnectionError:
    # exc_info=True anexa automaticamente o traceback completo na saída
    logger.error("Falha ao conectar ao banco de dados 'postgres_main' (request_id=%s)", req_id, exc_info=True)

try:
    send_email(recipient, subject, body)
except Exception:
    logger.error("Erro ao enviar e-mail para %s (notification_id=%s)", masked_email, notification_id, exc_info=True)
    raise
```

### Padrão para operações críticas: logue tentativa e resultado

```python
logger.info("Enviando e-mail para %s (notification_id=%s)", masked_email, notification_id)
try:
    send_email(recipient.email, subject, body)
    logger.info("E-mail enviado com sucesso para %s (notification_id=%s)", masked_email, notification_id)
except Exception:
    logger.error("Falha ao enviar e-mail para %s (notification_id=%s)", masked_email, notification_id, exc_info=True)
    raise
```

---

## ❌ Anti-Padrões (Don't)

```python
# ERRO: Gerenciar arquivos e rotação local dentro do container gera perda de dados
from logging.handlers import RotatingFileHandler
logger.addHandler(RotatingFileHandler("api.log", maxBytes=5000))

# ERRO: Exposição de PII e credenciais em texto claro
logger.info("O usuário Diego fez login com a senha admin123")

# ERRO: Uso de método depreciado (.warn)
logger.warn("Arquivo grande recebido")

# ERRO: print() ignora handlers, formatação e níveis configurados
print("Erro no banco")

# ERRO: Concatenação manual de string perde o stack trace estruturado
logger.error("Falha ao salvar: " + str(e))

# ERRO: Logar apenas a intenção, sem confirmar o resultado da operação
logger.debug("Enviando e-mail para %s", masked_email)
send_email(...)  # sem log de sucesso ou falha
```

---

## 🧠 Instruções de Ação para a IA (Code Review Workflow)

1. **Bloqueio de Escrita em Disco:** Varra o código em busca de `FileHandler`, `RotatingFileHandler`, `TimedRotatingFileHandler` ou escrita manual em arquivos para logs. Exija que todos os logs sejam direcionados para `sys.stdout`.
2. **Auditoria de Segurança:** Identifique PII ou credenciais sendo injetadas sem mascaramento na string do logger. Barre o código e exija uma função de mascaramento.
3. **Padrão de Mensagem Natural:** Garanta que as mensagens sejam frases legíveis em português (ou no idioma do projeto), descrevendo claramente o evento. Evite pares `chave='valor'` genéricos — prefira "E-mail enviado para u***@mail.com" a `event='email_sent' to='u***@mail.com'`.
4. **Substituição de Prints:** Force a alteração de qualquer `print()` no ciclo de vida da API para chamadas do logger configurado.
5. **Validação de Exceções:** Em blocos `except`, certifique-se de que os erros sejam registrados com `.error()` e contenham `exc_info=True`. Não aceite strings concatenadas manualmente.
6. **Verificação de Métodos Legados:** Se o código utilizar `logger.warn()`, force a alteração imediata para `logger.warning()`.
7. **Completude do Log:** Verifique se operações críticas (envio de e-mail, chamadas externas, escrita no banco) possuem log tanto de tentativa quanto de sucesso/falha — nunca apenas um dos dois.