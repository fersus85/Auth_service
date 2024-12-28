.PHONY: up install install-dev lint format down remove-images help

PYTHON = python3
BLACK_LINE_LENGTH = --line-length 79
SRC_DIR = src
IMAGES = fastapi:latest
TEST_PATH = $(CURDIR)/tests
ADMIN_COMPOSE_PATH = $(CURDIR)/Admin_panel/docker-compose.yml
MOVIE_COMPOSE_PATH = $(CURDIR)/Movies_API/docker-compose.yml


all: up

# Запуск приложения Auth
up-auth:
	@docker compose up -d --build

# Очистка после остановки приложения Auth
down-auth:
	@echo "Очистка временных файлов и контейнеров..."
	@docker compose down
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete

# Удаление выбранных образов
remove-images-auth:
	@echo "Удаление указанных образов..."
	@docker rmi $(IMAGES)

# Запуск приложения Admin
up-admin:
	@docker compose -f $(ADMIN_COMPOSE_PATH) up -d --build

# Очистка после остановки приложения Admin
down-admin:
	@echo "Очистка контейнеров..."
	@docker compose -f $(ADMIN_COMPOSE_PATH) down

# Запуск приложения Admin
up-movie:
	@docker compose -f $(MOVIE_COMPOSE_PATH) up -d --build

# Очистка после остановки приложения Admin
down-movie:
	@echo "Очистка контейнеров..."
	@docker compose -f $(MOVIE_COMPOSE_PATH) down

# Установка зависимостей продашен
install:
	@echo "Установка зависимостей..."
	@pip install -r requirements.txt

# Установка зависимостей dev
install-dev:
	@echo "Установка зависимостей..."
	@pip install -r requirements.txt
	@pip install -r requirements-dev.txt

# Линтинг
lint:
	@echo "Запуск линтинга с помощью flake8..."
	@$(PYTHON) -m flake8 $(SRC_DIR)
	@echo "All done! ✨ 🍰 ✨"

# Автоформатирование
format:
	@echo "Запуск форматирования с помощью black..."
	@$(PYTHON) -m black $(BLACK_LINE_LENGTH) $(SRC_DIR)

# Поднятие инфраструктуры тестов
test-up-auth:
	@docker compose --file docker-compose-tests.yml up -d --build
	@sleep 5
	@docker compose --file docker-compose-tests.yml exec fastapi-auth alembic upgrade head

# Запуск тестов
test-auth:
	@pip install -r tests/functional/requirements.txt >/dev/null
	PYTHONPATH=$(CURDIR)/src pytest tests/functional

# Остановка инфраструктуры тестов
test-down-auth:
	@docker compose --file docker-compose-tests.yml down

# Миграции
db/migrate-auth:
	@docker compose exec fastapi-auth alembic upgrade head

# Superuser
su-create:
	@docker exec -it auth-service-fastapi-auth-1 bash

# Откат миграции
db/downgrade-auth:
	@docker compose exec fastapi-auth alembic downgrade base

# Вывод справки
help:
	@echo "Доступные команды:"
	@echo "  make up-auth             - Запуск сервиса Auth"
	@echo "  make down-auth           - Остановка Auth и очиска"
	@echo "  make db/migrate-auth     - Миграция alembic Auth"
	@echo "  make db/downgrade-auth   - Откат миграции alembic Auth"
	@echo "  make su-create           - Подключение к Auth контейнеру для создания Superuser"
	@echo "  make up-admin            - Запуск сервиса Admin"
	@echo "  make down-admin          - Остановка Admin и очиска"
	@echo "  make up-movie            - Запуск сервиса Movies_API"
	@echo "  make down-movie          - Остановка Movies_API и очиска"
	@echo "  make install             - Установка зависимостей продакшен"
	@echo "  make install-dev         - Установка зависимостей dev"
	@echo "  make lint                - Запуск линтера"
	@echo "  make format              - Автоформатирование кода"
	@echo "  make test-up-auth        - Поднятие инфраструктуры тестов"
	@echo "  make tes-auth            - Запуск тестов"
	@echo "  make test-down-auth      - Остановка инфраструктуры тестов"
	@echo "  remove-images -auth      - Удаление указанных образов"
