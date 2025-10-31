# syntax=docker/dockerfile:1

#############################
# Backend (FastAPI) image
#############################
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg / build steps
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (directly from pyproject list)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        "dotenv>=0.9.9" \
        "neo4j>=6.0.2" \
        "notebook>=7.4.7" \
        "pandas>=2.3.3" \
        "psycopg2-binary>=2.9.11" \
        "pymongo>=4.15.3" \
        "qdrant-client>=1.15.1" \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.30.0" \
        "sqlalchemy[asyncio]>=2.0.36" \
        "asyncpg>=0.29.0" \
        "pydantic-settings>=2.5.2" \
        "passlib==1.7.4" \
        "bcrypt==4.0.1"

COPY app ./app
COPY sql ./sql
COPY main.py pyproject.toml uv.lock ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


#############################
# Frontend (Vite) image
#############################
FROM node:20-alpine AS frontend

WORKDIR /usr/src/app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
