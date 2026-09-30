.PHONY: help run-dev check test migrate migrations collectstatic shell

PYTHON ?= .venv/bin/python
MANAGE := $(PYTHON) manage.py

# Local development defaults. Production settings live in
# /etc/gastbok/gastbok.env on the Raspberry Pi (see docs/deploy/).
DJANGO_SECRET_KEY ?= dev-secret-key
DJANGO_DEBUG ?= True
HOST ?= 0.0.0.0
PORT ?= 8000

ENV := DJANGO_SECRET_KEY="$(DJANGO_SECRET_KEY)" DJANGO_DEBUG="$(DJANGO_DEBUG)"

help:
	@echo "Gästbok"
	@echo ""
	@echo "  make run-dev        Start the development server on $(HOST):$(PORT)"
	@echo "  make test           Run the test suite"
	@echo "  make check          Run Django system checks"
	@echo "  make migrate        Apply migrations"
	@echo "  make migrations     Create migrations"
	@echo "  make collectstatic  Collect static files"
	@echo "  make shell          Open the Django shell"

run-dev:
	$(ENV) $(MANAGE) runserver $(HOST):$(PORT)

check:
	$(ENV) $(MANAGE) check

test:
	$(ENV) $(MANAGE) test

migrate:
	$(ENV) $(MANAGE) migrate

migrations:
	$(ENV) $(MANAGE) makemigrations

collectstatic:
	$(ENV) $(MANAGE) collectstatic --noinput

shell:
	$(ENV) $(MANAGE) shell
