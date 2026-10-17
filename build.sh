#!/usr/bin/env bash
#
# Render build step for the Madrasa web app.
#
# A custom buildCommand REPLACES Render's default Python build, so this script
# installs dependencies itself and then prepares the database and static files.
# All environment (DJANGO_ENV=production, DATABASE_URL, DJANGO_SECRET_KEY,
# DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS, ...) is injected by Render
# from render.yaml BEFORE this runs, so the production settings load and their
# fail-closed checks pass.

set -o errexit
set -o pipefail
set -o nounset

# The settings package selects production.py from DJANGO_ENV (see render.yaml).
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-madrasa_sys.settings}"
export PYTHONUNBUFFERED=1

echo "==> Python $(python --version 2>&1)"
echo "==> pip $(python -m pip --version 2>&1)"

echo "==> Installing dependencies"
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt

echo "==> Verifying Django configuration"
# Fails the build early if settings/apps are misconfigured.
python manage.py check

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Build complete"
