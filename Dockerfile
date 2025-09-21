# ===============================
# Proyecto Maestro(s) — Dockerfile
# ===============================

# ---- Base ----
FROM python:3.13-slim AS base

# Evitar bytecode y buffering en contenedores
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
# - libpq-dev + gcc: necesarios para psycopg2
# - curl + build-essential: soporte general de compilación
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_VERSION=1.8.3
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# ---- Dependencias ----
# Copiar solo los archivos de dependencias primero (mejor cache)
COPY pyproject.toml poetry.lock* ./

# Instalar dependencias (sin instalar en editable mode)
RUN poetry install --no-root --no-interaction --no-ansi

# ---- App ----
# Copiar el resto del código
COPY . .

# Variables de entorno por defecto
ENV PORT=5000
ENV HOST=0.0.0.0

# Exponer puerto Flask/Gunicorn
EXPOSE ${PORT}

# ---- Comando por defecto ----
# Usamos gunicorn en producción
CMD ["poetry", "run", "gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "app.web.flask_app:app"]
