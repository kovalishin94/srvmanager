#!/bin/bash
set -e

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Запускаем Gunicorn..."
exec gunicorn mangoapi.wsgi:application --bind 0.0.0.0:8000 --workers 3