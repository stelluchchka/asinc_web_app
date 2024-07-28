#!/bin/sh

alembic downgrade base
alembic upgrade febb240d2824
alembic upgrade f740eee31c1d

exec "$@"
