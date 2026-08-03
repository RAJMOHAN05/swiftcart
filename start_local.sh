#!/usr/bin/env bash
set -Eeuo pipefail

SWIFTCART_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SWIFTCART_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Creating SwiftCart virtual environment..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

echo "Preparing database..."
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_store

echo "SwiftCart is starting at http://127.0.0.1:8000/"
echo "Press Control+C to stop the server."
.venv/bin/python manage.py runserver
