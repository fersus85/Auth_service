.PHONY: up install install-dev lint format down remove-images help

PYTHON = python3
BLACK_LINE_LENGTH = --line-length 79
SRC_DIR = src
IMAGES = fastapi:latest
TEST_PATH = $(CURDIR)/tests


all: up

# Запуск приложения
up:
	@docker compose up -d --build

# Очистка после остановки приложения
down:
	@echo "Очистка временных файлов и контейнеров..."
	@docker compose down -v
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete

# Удаление выбранных образов
remove-images:
	@echo "Удаление указанных образов..."
	@docker rmi $(IMAGES)

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
test-up:
	@docker compose --file docker-compose-tests.yml up -d --build
	@sleep 5

# Запуск тестов
test:
	@pip install -r tests/functional/requirements.txt >/dev/null
	@export PYTHONPATH=$(CURDIR)
	@pytest tests/functional/src/

# Остановка инфраструктуры тестов
test-down:
	@docker compose --file docker-compose-tests.yml down

# Вывод справки
help:
	@echo "Доступные команды:"
	@echo "  make up             - Запуск приложения"
	@echo "  make down           - Остановка приложения и очиска"
	@echo "  make install        - Установка зависимостей продакшен"
	@echo "  make install-dev    - Установка зависимостей dev"
	@echo "  make lint           - Запуск линтера"
	@echo "  make format         - Автоформатирование кода"
	@echo "  make test-up        - Поднятие инфраструктуры тестов"
	@echo "  make test-down      - Запуск тестов"
	@echo "  make test           - Остановка инфраструктуры тестов"
	@echo "  remove-images       - Удаление указанных образов"
