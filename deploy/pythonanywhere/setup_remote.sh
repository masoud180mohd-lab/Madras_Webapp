#!/bin/bash
# Inaendeshwa kwenye PythonAnywhere (Bash console au scheduled task).
set -euo pipefail
PROJECT="${PA_PROJECT_HOME:-/home/rasulillahmadras/madrasa_sys}"
cd "$PROJECT"
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  python3.13 -m venv .venv || python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -U pip
fi
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo "SETUP_OK"
