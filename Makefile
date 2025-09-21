# ==============================
# Proyecto Maestro(s) — Makefile
# ==============================
# Requiere: Poetry, Docker (opcional), psql (opcional para db-init)
# Usa .env si existe (POSTGRES_*, FLASK_ENV, etc.)

# -------- Variables --------
POETRY        ?= poetry
MODULE        ?= app.web.flask_app          # para "python -m ..."
WSGI_APP      ?= app.web.flask_app:app      # para gunicorn
HOST          ?= 0.0.0.0
PORT          ?= 5000
IMAGE_NAME    ?= proyecto-maestros
CONTAINER_NAME?= pm-app
ENV_FILE      ?= .env

# Carga variables desde .env si existe
ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

# -------- Ayuda --------
.PHONY: help
help:
	@echo "Comandos principales:"
	@echo "  make install        -> Instala dependencias con Poetry"
	@echo "  make run-dev        -> Ejecuta en dev: python -m $(MODULE)"
	@echo "  make run            -> Ejecuta en prod con gunicorn"
	@echo "  make test           -> Corre tests (pytest)"
	@echo "  make format         -> Formatea (black)"
	@echo "  make lint           -> Linter (flake8)"
	@echo "  make clean          -> Limpia __pycache__/pyc"
	@echo "  make db-init        -> Aplica scripts/init_db.sql (via psql)"
	@echo "  make docker-build   -> Construye imagen Docker"
	@echo "  make docker-run     -> Levanta contenedor"
	@echo "  make docker-logs    -> Logs del contenedor"
	@echo "  make docker-stop    -> Para y elimina contenedor"
	@echo "  make docker-rmi     -> Elimina imagen"
	@echo "  make dev-setup      -> Agrega black/flake8/pytest al grupo dev"

# -------- Local --------
.PHONY: install
install:
	@command -v $(POETRY) >/dev/null 2>&1 || { echo "Poetry no encontrado; instalando..."; pip3 install poetry; }
	$(POETRY) install --no-root

.PHONY: dev-setup
dev-setup:
	$(POETRY) add --group dev black flake8 pytest

.PHONY: run-dev
run-dev:
	$(POETRY) run python -m $(MODULE)

# Alternativa con el CLI de Flask (opcional)
.PHONY: run-flask
run-flask:
	$(POETRY) run flask --app $(MODULE) --debug run --host=$(HOST) --port=$(PORT)

.PHONY: run
run:
	$(POETRY) run gunicorn -w 3 -b $(HOST):$(PORT) "$(WSGI_APP)"

.PHONY: test
test:
	$(POETRY) run pytest -q

.PHONY: format
format:
	$(POETRY) run black app tests

.PHONY: lint
lint:
	$(POETRY) run flake8 app tests

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +

# -------- Base de datos (opcional) --------
# Requiere psql instalado y variables en .env:
# POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
.PHONY: db-init
db-init:
	@[ -f scripts/init_db.sql ] || { echo "No existe scripts/init_db.sql"; exit 1; }
	@[ -n "$(POSTGRES_HOST)" ] || { echo "Falta POSTGRES_HOST en .env"; exit 1; }
	@[ -n "$(POSTGRES_DB)" ]   || { echo "Falta POSTGRES_DB en .env"; exit 1; }
	@[ -n "$(POSTGRES_USER)" ] || { echo "Falta POSTGRES_USER en .env"; exit 1; }
	@[ -n "$(POSTGRES_PASSWORD)" ] || { echo "Falta POSTGRES_PASSWORD en .env"; exit 1; }
	PGPASSWORD=$(POSTGRES_PASSWORD) psql \
		-h $(POSTGRES_HOST) -p $${POSTGRES_PORT:-5432} \
		-U $(POSTGRES_USER) -d $(POSTGRES_DB) \
		-f scripts/init_db.sql

# -------- Docker --------
.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE_NAME) .

.PHONY: docker-run
docker-run: docker-stop
	docker run -d --name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		--env-file $(ENV_FILE) \
		$(IMAGE_NAME)

.PHONY: docker-logs
docker-logs:
	docker logs -f $(CONTAINER_NAME)

.PHONY: docker-stop
docker-stop:
	-@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true

.PHONY: docker-rmi
docker-rmi:
	-@docker rmi $(IMAGE_NAME) 2>/dev/null || true
