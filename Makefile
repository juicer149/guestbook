.PHONY: run-dev migrate migrations shell test

DJANGO_SECRET_KEY ?= dev-secret-key
DJANGO_DEBUG ?= True
HOST ?= 0.0.0.0
PORT ?= 8000

run-dev:
	DJANGO_SECRET_KEY="$(DJANGO_SECRET_KEY)" \
	DJANGO_DEBUG="$(DJANGO_DEBUG)" \
	python manage.py runserver $(HOST):$(PORT)

migrations:
	DJANGO_SECRET_KEY="$(DJANGO_SECRET_KEY)" \
	DJANGO_DEBUG="$(DJANGO_DEBUG)" \
	python manage.py makemigrations

migrate:
	DJANGO_SECRET_KEY="$(DJANGO_SECRET_KEY)" \
	DJANGO_DEBUG="$(DJANGO_DEBUG)" \
	python manage.py migrate

shell:
	DJANGO_SECRET_KEY="$(DJANGO_SECRET_KEY)" \
	DJANGO_DEBUG="$(DJANGO_DEBUG)" \
	python manage.py shell

test:
	DJANGO_SECRET_KEY="$(DJANGO_SECRET_KEY)" \
	DJANGO_DEBUG="$(DJANGO_DEBUG)" \
	python manage.py test
