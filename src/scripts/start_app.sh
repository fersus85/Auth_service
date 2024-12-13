#!/usr/bin/env bash

set -e

echo "Генерация миграций..."
alembic revision --autogenerate -m "migrate models"

sleep 1

echo "Применяем миграции..."
alembic upgrade head

sleep 1
echo "Запуск приложения..."
exec "$@"
