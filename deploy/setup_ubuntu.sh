#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run with sudo: sudo bash deploy/setup_ubuntu.sh"
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip nginx postgresql postgresql-contrib \
  libpq-dev git curl build-essential

id swiftcart >/dev/null 2>&1 || useradd --system --create-home --shell /bin/bash swiftcart
install -d -o swiftcart -g www-data -m 775 /srv/swiftcart

cp deploy/swiftcart.service /etc/systemd/system/swiftcart.service
cp deploy/nginx.conf /etc/nginx/sites-available/swiftcart
cp deploy/swiftcart-sudoers /etc/sudoers.d/swiftcart-deploy
chmod 440 /etc/sudoers.d/swiftcart-deploy
visudo -cf /etc/sudoers.d/swiftcart-deploy
ln -sfn /etc/nginx/sites-available/swiftcart /etc/nginx/sites-enabled/swiftcart
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable swiftcart nginx postgresql
nginx -t

echo "Base packages are ready."
echo "Next: copy the repository to /srv/swiftcart, create .env and PostgreSQL credentials,"
echo "then run deploy/deploy.sh. Follow deploy/README_AWS.md."
