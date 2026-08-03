#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/srv/swiftcart"
VENV_DIR="$APP_DIR/.venv"

test -d "$APP_DIR/.git" || {
  echo "Missing Git repository at $APP_DIR"
  exit 1
}
test -f "$APP_DIR/.env" || {
  echo "Missing production environment file at $APP_DIR/.env"
  exit 1
}

git fetch --prune origin main
git checkout main
git pull --ff-only origin main

"$VENV_DIR/bin/pip" install --disable-pip-version-check -r requirements.txt
"$VENV_DIR/bin/python" manage.py migrate --noinput
"$VENV_DIR/bin/python" manage.py collectstatic --noinput
"$VENV_DIR/bin/python" manage.py check --deploy

sudo systemctl restart swiftcart
sudo systemctl reload nginx
curl --fail --retry 5 --retry-delay 2 http://127.0.0.1:8000/health/
