#!/bin/bash
set -e

echo "Применяем миграции..."
python manage.py makemigrations --noinput

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Запускаем Gunicorn..."
python manage.py runserver 0.0.0.0:8000