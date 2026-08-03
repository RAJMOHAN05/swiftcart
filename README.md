# SwiftCart Phase 2 — Smart Django E-Commerce

SwiftCart is a placement-ready Django e-commerce platform with a polished,
responsive storefront, explainable recommendations, operational analytics,
customer support, PWA installation and production deployment automation.

## Phase 2 features

- **AI product recommendations** — a local hybrid scoring engine combines
  browsing history, wishlist categories, order history, ratings, sales
  popularity, freshness and featured-product signals. Each recommendation
  includes an explanation; no paid external AI API is required.
- **Admin analytics dashboard** — modern SwiftCart-branded Django admin plus
  date filtering, revenue trend, order-status chart, category revenue, top
  products, average order value, customer count and low-stock alerts.
- **Sales and revenue reports** — staff-only order ledger, UPI UTR/reference
  visibility, totals and filtered CSV export.
- **PDF invoice download** — branded, access-controlled invoice generated with
  ReportLab for each order.
- **Email order confirmation** — HTML and plain-text email after a successful
  checkout, plus status-update emails.
- **Wishlist animations** — AJAX add/remove, heart animation, toast feedback
  and live wishlist count without a page reload.
- **Ratings and reviews** — one review per user, averaged product rating and a
  server-enforced delivered-purchase requirement. The review form unlocks only
  after the customer's matching order reaches `Delivered`.
- **Advanced search and filters** — keyword/category search, minimum and
  maximum price, rating, stock availability, six sorting options and
  pagination.
- **Order tracking timeline** — generated tracking ID, estimated delivery,
  persisted status events, locations and live customer notifications.
- **Live chat support** — session-backed guest/customer chat, immediate
  assistant responses, four-second update polling and a staff support inbox.
- **Real-time notifications** — 15-second notification polling, unread badge,
  order updates and support-reply alerts.
- **PWA** — root service worker, offline screen, install prompt, app manifest,
  maskable icon and shortcuts.
- **AWS deployment** — Ubuntu EC2, PostgreSQL, Gunicorn, systemd, Nginx and HTTPS
  instructions in `deploy/README_AWS.md`.
- **GitHub Actions CI/CD** — PostgreSQL tests, migration validation, static
  build, Docker build and verified-main deployment to EC2.

## Technology

- Python 3.13 and Django 6
- SQLite locally; PostgreSQL in Docker and production
- ReportLab for invoices
- Bootstrap, custom responsive CSS, vanilla JavaScript and Chart.js
- Gunicorn, WhiteNoise, Nginx, Docker and GitHub Actions

## Clean local setup

### Fastest start on macOS/Linux

```bash
chmod +x start_local.sh
./start_local.sh
```

The launcher creates `.venv` when needed, installs dependencies, applies
migrations, loads demo products and starts the local server.

### Manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_store
python manage.py createsuperuser
python manage.py runserver
```

Open:

- Store: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Customer dashboard: `http://127.0.0.1:8000/accounts/dashboard/`
- Staff analytics: `http://127.0.0.1:8000/accounts/seller/`
- Sales report: `http://127.0.0.1:8000/accounts/seller/reports/`
- Support inbox: `http://127.0.0.1:8000/support/inbox/`
- Health check: `http://127.0.0.1:8000/health/`

Demo coupon: `RAJ10`

The seed command is idempotent and can safely be run again.

See `VERIFICATION.md` for the feature-by-feature test matrix and latest results.

### If an older design is still visible

Version 6 automatically replaces old SwiftCart service-worker caches and uses
versioned CSS/JavaScript URLs. Open the site once and refresh after the automatic
reload. If Chrome still shows an old tab, close that tab and reopen
`http://127.0.0.1:8000/`.

## Email setup

Local development uses Django's console email backend, so confirmation emails
appear in the terminal. To send real emails, copy `.env.example` to `.env`,
replace the SMTP values, then load them before starting Django:

```bash
set -a
source .env
set +a
python manage.py runserver
```

Never commit real credentials.

For Gmail, an app password is required when two-factor authentication is
enabled. A normal account password should not be used.

## Docker with PostgreSQL

```bash
docker compose up --build
```

The web service waits for PostgreSQL, applies committed migrations, loads the
demo catalogue and starts Gunicorn.

## Tests and release checks

```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

The included suite covers catalogue filters, recommendations, AJAX wishlist,
cart/coupon behaviour, checkout email, tracking events, private PDF invoices,
real-time order notifications, admin reporting and customer support chat.

## AWS EC2 and CI/CD

Read `deploy/README_AWS.md`. It includes the security-group rules, PostgreSQL
creation, production environment variables, systemd/Nginx setup, Certbot HTTPS,
GitHub environment secrets and health checks.

The GitHub deployment workflow expects:

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`

Actual AWS provisioning and external email delivery require your own AWS
account, domain/server values and SMTP credentials. No secret or account
credential is included in this repository.

## Important payment note

The checkout contains Cash on Delivery and a demo UPI workflow. A real payment
gateway requires a merchant account, server-side signature verification and
webhooks before it can be used for production payments. Never treat a
client-entered UPI reference as verified payment.
