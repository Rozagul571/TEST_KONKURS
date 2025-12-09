# Makefile
.PHONY: help setup migrate superuser run-all docker-up

run-bot:
	python3 -m bots.main_bot.main

runserver:
	python manage.py runserver 8000

run fastapi:
	uvicorn fastapi_app.main:app --reload --host 0.0.0.0 --port 8001

#run-user:

unicorn:
	uvicorn fastapi_app.main:app --reload --host 0.0.0.0 --port 8001
help:
	@echo "setup → venv + pip"
	@echo "migrate → DB"
	@echo "superuser → admin"
	@echo "docker-up → hamma"

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

superuser:
	. venv/bin/activate && python manage.py createsuperuser

docker-up:
	docker-compose -f docker/docker-compose.yml up --build

mig:
	python manage.py makemigrations core
	python manage.py migrate

log:
	tail -f debug.log