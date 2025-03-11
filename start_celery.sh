#!/bin/bash
set -e

exec celery -A srvmanager worker --loglevel=INFO