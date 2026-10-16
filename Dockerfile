FROM python:3.13.3-slim as builder

WORKDIR /opt

# Evita arquivos .pyc e garante logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m venv venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13.3-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y curl libmagic1 && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

WORKDIR /app

COPY --chown=appuser:appgroup ./alembic.ini ./alembic.ini
COPY --chown=appuser:appgroup ./alembic ./alembic
COPY --chown=appuser:appgroup ./app ./app

EXPOSE 8000

# Workers configurável via variável de ambiente, padrão 1
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1} --no-access-log"]