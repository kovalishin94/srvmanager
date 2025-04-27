#!/bin/bash
set -e

exec celery -A srvmanager worker --concurrency=4 --loglevel=INFO