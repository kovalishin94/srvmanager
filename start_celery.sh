#!/bin/bash
set -e

exec celery -A srvmanager worker --concurrency=${CELERY_WORKERS} --prefetch-multiplier=1 --loglevel=INFO