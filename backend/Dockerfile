FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev wget \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Install dependencies with explicit psycopg2 binary for production
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir "psycopg2-binary>=2.9" && \
    pip install --no-cache-dir ".[prod]"

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY wait-for-db.sh ./
COPY entrypoint.sh ./
RUN chmod +x ./wait-for-db.sh ./entrypoint.sh

CMD ["sh", "-c", "./entrypoint.sh"]
