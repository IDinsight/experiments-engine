#!/bin/bash
python -m alembic upgrade head
exec gunicorn -k app.Worker -w 4 -b 0.0.0.0:8000 --preload \
    -c gunicorn_hooks_config.py app:app
#
