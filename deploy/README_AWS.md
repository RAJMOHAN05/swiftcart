# SwiftCart AWS EC2 deployment

This production layout uses one Ubuntu EC2 instance, PostgreSQL, Gunicorn,
Nginx, HTTPS and GitHub Actions. For higher traffic, move PostgreSQL to Amazon
RDS and keep the same Django environment variables.

## 1. Create the EC2 instance

1. Launch Ubuntu 24.04 LTS (t3.micro is suitable for a demo).
2. Allow SSH (22) only from your IP, and HTTP/HTTPS (80/443) publicly.
3. Attach an Elastic IP if the address must remain stable.
4. SSH to the instance and clone this repository into your Ubuntu home folder.

## 2. Install the server services

From that temporary clone:

```bash
sudo bash deploy/setup_ubuntu.sh
sudo cp -a . /srv/swiftcart/
sudo chown -R swiftcart:www-data /srv/swiftcart
sudo -u swiftcart python3 -m venv /srv/swiftcart/.venv
```

Replace `YOUR_DOMAIN_OR_EC2_IP` in `/etc/nginx/sites-available/swiftcart`.

## 3. Create PostgreSQL

Generate a strong password and run:

```bash
sudo -u postgres psql
CREATE DATABASE swiftcart;
CREATE USER swiftcart WITH ENCRYPTED PASSWORD 'REPLACE_WITH_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE swiftcart TO swiftcart;
\c swiftcart
GRANT ALL ON SCHEMA public TO swiftcart;
\q
```

## 4. Configure production secrets

Create `/srv/swiftcart/.env` owned by `swiftcart`, mode `600`:

```dotenv
DJANGO_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=YOUR_DOMAIN_OR_EC2_IP
DJANGO_CSRF_TRUSTED_ORIGINS=https://YOUR_DOMAIN
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
SITE_URL=https://YOUR_DOMAIN
DB_ENGINE=postgres
POSTGRES_DB=swiftcart
POSTGRES_USER=swiftcart
POSTGRES_PASSWORD=REPLACE_WITH_A_STRONG_PASSWORD
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL="SwiftCart <orders@YOUR_DOMAIN>"
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=YOUR_SMTP_USERNAME
EMAIL_HOST_PASSWORD=YOUR_SMTP_APP_PASSWORD
EMAIL_USE_TLS=True
```

Do not commit this file.

## 5. First launch

```bash
cd /srv/swiftcart
bash deploy/deploy.sh
/srv/swiftcart/.venv/bin/python manage.py createsuperuser
sudo systemctl enable --now swiftcart nginx
```

Add HTTPS with Certbot after the domain points to the Elastic IP:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d YOUR_DOMAIN
```

## 6. GitHub Actions CD

Copy the public deployment key to
`/home/swiftcart/.ssh/authorized_keys` and keep the matching private key only in
GitHub. Then add these GitHub environment secrets under the `production`
environment:

- `EC2_HOST`: Elastic IP or domain
- `EC2_USER`: `swiftcart`
- `EC2_SSH_KEY`: the private deployment key

The CI workflow tests migrations, PostgreSQL, Django, static assets and the
Docker build. A successful main-branch CI run triggers the EC2 deployment
workflow, which runs `deploy/deploy.sh` and verifies `/health/`.

## Useful checks

```bash
sudo systemctl status swiftcart
sudo journalctl -u swiftcart -n 100 --no-pager
sudo nginx -t
curl -I https://YOUR_DOMAIN/health/
```
