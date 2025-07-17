#!/bin/bash
set -e

exec celery -A srvmanager worker --concurrency=${CELERY_WORKERS} --loglevel=INFO