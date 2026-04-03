# 🚀 Space Resource Exchange (SRX)

A contract exchange platform for space resources — lunar ice, helium-3, asteroid metals, and beyond. Built with **Python + FastAPI**, deployable on **Render**.

## Features

- **Contract Types**: Regular, Option (CALL/PUT), and Smart Contract (metadata)
- **Space Resources**: Lunar Ice, Helium-3, Platinum Group Metals, Regolith, Iron-Nickel Ore, Solar Energy Credits, Carbonaceous Compounds
- **Offers/Bids**: Submit, accept, reject, or withdraw offers
- **Payment Methods**: Stripe checkout, internal credits ledger, and crypto wallet addresses
- **Space-Themed UI**: Dark starfield background, neon accents, animated planet

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | PostgreSQL (Render) / SQLite (local dev) |
| Templates | Jinja2 |
| Payments | Stripe SDK |
| Deployment | Render (render.yaml + Dockerfile) |

## Local Development

### Prerequisites

- Python 3.11+
- (Optional) PostgreSQL for production-like testing

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Codesurfing10/SPACEREASOURCEEXCHANGE.git
cd SPACEREASOURCEEXCHANGE

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment variables
cp .env.example .env
# Edit .env to add your Stripe keys (optional for MVP)

# 5. Run the application
uvicorn app.main:app --reload
```

The app will be available at **http://localhost:8000**.

> **Note**: SQLite is used by default for local development. The database file `space_exchange.db` is created automatically. No migration step is required locally — SQLAlchemy creates all tables on startup.

### Running with PostgreSQL locally

```bash
# Set DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/space_exchange

# Run migrations
alembic upgrade head

# Start the app
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy-compatible DB URL | Yes (defaults to SQLite) |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_live_...` or `sk_test_...`) | No (Stripe disabled if empty) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key for frontend | No |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | No |
| `APP_BASE_URL` | Public base URL for Stripe redirect URLs | No (defaults to `http://localhost:8000`) |
| `DEBUG` | Enable FastAPI debug mode | No |

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

The tests use an isolated SQLite database (`test_space.db`) which is cleaned up after the test session.

## API Reference

### Contracts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/contracts/` | List contracts (filterable) |
| `POST` | `/api/contracts/` | Create a contract |
| `GET` | `/api/contracts/{id}` | Get contract details |
| `PATCH` | `/api/contracts/{id}/status` | Update contract status |
| `GET` | `/api/contracts/{id}/offers` | List offers for a contract |
| `PATCH` | `/api/contracts/{id}/offers/{offer_id}/accept` | Accept an offer |

### Offers

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/offers/{contract_id}` | Submit an offer |
| `PATCH` | `/api/offers/{offer_id}/withdraw` | Withdraw an offer |

### Payments

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/payments/{contract_id}/preference` | Add payment preference |
| `GET` | `/api/payments/{contract_id}/preferences` | List payment preferences |
| `POST` | `/api/payments/{contract_id}/stripe-session` | Create Stripe checkout session |

### Pages

| Path | Description |
|------|-------------|
| `/` | Landing page |
| `/contracts` | Browse contracts (with filters) |
| `/contracts/new` | Create a new contract form |
| `/contracts/{id}` | Contract detail page with offers |

## Deploying to Render

The repository includes a **Render Blueprint** (`render.yaml`) that provisions a Python web service and a managed PostgreSQL database in one click.

### Blueprint Deploy (recommended)

1. **Fork** this repository to your GitHub account.
2. Go to the [Render Dashboard](https://dashboard.render.com/) and click **New → Blueprint**.
3. Connect your GitHub account and select your forked repository.
4. Render detects `render.yaml` and proposes two resources:
   - **`space-resource-exchange`** — Python web service
   - **`space-resource-exchange-db`** — Managed PostgreSQL (free tier)
5. Click **Apply**. Render will:
   - Install Python dependencies (`pip install -r requirements.txt`)
   - Run database migrations automatically via `preDeployCommand: alembic upgrade head`
   - Start the app with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. After the first successful deploy, set the **required secrets** in the web service's **Environment** tab (see table below).
7. Open the service URL shown in the dashboard — your live app is ready. 🚀

### Required environment variables

| Variable | Where to get it | Notes |
|----------|-----------------|-------|
| `DATABASE_URL` | Set automatically by Render from the linked database | Do **not** set manually when using Blueprint |
| `STRIPE_SECRET_KEY` | [Stripe Dashboard → API keys](https://dashboard.stripe.com/apikeys) | Use `sk_test_…` for testing, `sk_live_…` for production |
| `STRIPE_PUBLISHABLE_KEY` | Stripe Dashboard → API keys | Use `pk_test_…` / `pk_live_…` accordingly |
| `STRIPE_WEBHOOK_SECRET` | [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks) | Create a webhook pointing to `https://<your-service>.onrender.com/api/payments/webhook` |
| `APP_BASE_URL` | Your Render service URL | e.g. `https://space-resource-exchange.onrender.com` — used for Stripe redirect URLs |
| `PYTHON_VERSION` | — | Pre-set to `3.11.0` in `render.yaml`; change if needed |

> **Stripe optional**: leaving all three Stripe variables empty disables Stripe checkout. The platform still works with internal credits and crypto-wallet payment methods.

### Manual deploy (without Blueprint)

1. **Create a PostgreSQL database** on Render (free tier available).
2. **Create a Web Service**:
   - Environment: **Python**
   - Build Command: `pip install -r requirements.txt`
   - Pre-Deploy Command: `alembic upgrade head`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/`
3. **Set environment variables** in the Render dashboard:
   - `DATABASE_URL` — copy the *Internal Database URL* from the Render PostgreSQL instance
   - `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` (optional)
   - `APP_BASE_URL` — your Render web service URL

### Docker deploy (local/self-hosted)

```bash
docker build -t space-resource-exchange .
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///./space_exchange.db" \
  space-resource-exchange
```

## Contract Flow

```
Seller creates contract (DRAFT/OPEN)
         ↓
Buyers submit offers (PENDING)
         ↓
Seller accepts best offer → contract ACCEPTED, other offers REJECTED
         ↓
Seller marks contract CLOSED (delivery complete)
```

## Option Contracts

For OPTION contracts, additional fields are available:
- **Option Type**: CALL (right to buy) or PUT (right to sell)
- **Strike Price**: The agreed execution price
- **Premium**: The option premium paid by the buyer
- **Expiration Date**: When the option expires

## Smart Contracts

SMART contract type records blockchain metadata:
- **Chain**: e.g., Ethereum, Polygon, Solana
- **Contract Address**: The deployed on-chain contract address

> ⚠️ No on-chain execution is performed by this platform (MVP scope). The blockchain metadata is informational.

## Payment Methods

| Method | Description |
|--------|-------------|
| **Stripe** | Card payment via Stripe Checkout. Requires `STRIPE_SECRET_KEY`. |
| **Credits** | Internal ledger placeholder. Specify a credits account handle. |
| **Crypto Wallet** | Record a wallet address. No on-chain transaction performed. |

## Project Structure

```
SPACEREASOURCEEXCHANGE/
├── app/
│   ├── main.py            # FastAPI app + startup
│   ├── config.py          # Settings (pydantic-settings)
│   ├── database.py        # SQLAlchemy engine + session
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── routes/
│   │   ├── pages.py       # HTML page routes (Jinja2)
│   │   ├── contracts.py   # REST API: contracts
│   │   ├── offers.py      # REST API: offers
│   │   └── payments.py    # REST API: payments + Stripe
│   ├── templates/
│   │   ├── base.html      # Base layout (starfield, navbar)
│   │   ├── index.html     # Landing page
│   │   └── contracts/
│   │       ├── list.html  # Browse/filter contracts
│   │       ├── detail.html # Contract detail + offers
│   │       └── create.html # Create contract form
│   └── static/
│       ├── css/main.css   # Space-themed stylesheet
│       └── js/main.js     # Starfield animation + UI
├── alembic/               # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── tests/
│   └── test_app.py        # Pytest smoke + endpoint tests
├── alembic.ini
├── requirements.txt
├── render.yaml            # Render Blueprint config
├── Dockerfile
├── .env.example
└── README.md
```