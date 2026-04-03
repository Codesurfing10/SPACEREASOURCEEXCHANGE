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

### One-Click Blueprint Deploy (Recommended)

1. **Fork** this repository to your GitHub account.
2. Go to [Render Dashboard](https://dashboard.render.com/) and sign in (or create a free account).
3. Click **New → Blueprint**.
4. Click **Connect a repository** and select your fork.
5. Render reads `render.yaml` and automatically provisions:
   - A **Python web service** (`space-resource-exchange`)
   - A **managed PostgreSQL database** (`space-resource-exchange-db`, free tier)
6. After the initial deploy completes, set the remaining environment variables under the web service **Environment** tab:
   - `STRIPE_SECRET_KEY` — your Stripe secret key (e.g. `sk_test_...`)
   - `STRIPE_PUBLISHABLE_KEY` — your Stripe publishable key (e.g. `pk_test_...`)
   - `APP_BASE_URL` — the Render service URL (e.g. `https://space-resource-exchange.onrender.com`)
7. Click **Save Changes** — Render will redeploy automatically.
8. Open the service URL in your browser to view the UI.

> **`DATABASE_URL` is wired automatically** from the Render database via `render.yaml`; you do not need to set it manually.

### Manual Deploy (Step-by-Step)

1. **Create a PostgreSQL database** on Render:
   - Dashboard → **New → PostgreSQL** → choose *Free* plan → **Create Database**.
   - Note the **Internal Database URL** shown on the database info page.
2. **Create a Web Service**:
   - Dashboard → **New → Web Service** → connect your repository.
   - Set **Environment**: `Python 3`.
   - Set **Build Command**: `pip install -r requirements.txt`
   - Set **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Set environment variables** in the web service **Environment** tab:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | Internal Database URL from step 1 |
   | `STRIPE_SECRET_KEY` | `sk_test_...` or `sk_live_...` from Stripe Dashboard |
   | `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` or `pk_live_...` from Stripe Dashboard |
   | `APP_BASE_URL` | Your Render service URL (e.g. `https://my-srx.onrender.com`) |
   | `PYTHON_VERSION` | `3.11.0` |

4. Click **Create Web Service**. Render builds the image, runs `alembic upgrade head`, then starts the server.

### Docker Deploy

```bash
docker build -t space-resource-exchange .
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///./space_exchange.db" \
  space-resource-exchange
```

## Viewing the UI

Once the app is running (locally at `http://localhost:8000` or on Render), open your browser and navigate to the routes below.

| Route | Description |
|-------|-------------|
| `/` | **Landing page** — space-themed hero, animated starfield, quick links |
| `/contracts` | **Browse contracts** — filter by resource type, contract type, status; paginated list |
| `/contracts/new` | **Create a contract** — form to post a new Regular, Option, or Smart contract |
| `/contracts/{id}` | **Contract detail** — view terms, submit/accept/reject offers, add payment preferences |
| `/docs` | **Interactive API docs** (Swagger UI) — explore and test all REST endpoints |
| `/redoc` | **ReDoc API docs** — alternative REST API reference |

### Quick Start on Render

1. After deployment, Render shows your live URL in the service dashboard (e.g. `https://space-resource-exchange.onrender.com`).
2. Click the URL — the space-themed landing page loads.
3. Go to `/contracts` to see the contract list (empty on first deploy — create one at `/contracts/new`).
4. Fill in the **Create Contract** form and submit — your contract appears in the list.
5. Open the contract detail page, submit an offer, then accept it to walk through the full flow.

## Troubleshooting (Render)

### ❌ Deploy fails — "connection refused" or database errors

**Cause**: The web service started before the database was ready, or `DATABASE_URL` is not set.

**Fix**:
1. In the Render dashboard, go to your web service → **Environment**.
2. Confirm `DATABASE_URL` is present. If you used the Blueprint deploy it is auto-wired; if not, paste the **Internal Database URL** from the Render PostgreSQL instance.
3. Re-deploy (Manual Deploy → **Deploy latest commit**).

### ❌ `Table does not exist` / 500 errors after deploy

**Cause**: Alembic migrations did not run.

**Fix**:
1. Check the web service **Logs** — look for `alembic upgrade head` output near startup.
2. If you see an Alembic error, verify that `DATABASE_URL` points to the correct database.
3. Alternatively, open a Render **Shell** for the service and run:
   ```bash
   alembic upgrade head
   ```
4. Restart the service.

### ❌ Static files not loading (CSS/JS missing, unstyled page)

**Cause**: Render may serve from a different working directory, or the `app/static` path is wrong.

**Fix**:
1. Ensure the start command is run from the repository root (the default for Render web services).
2. Confirm `app/static/css/main.css` and `app/static/js/main.js` exist in the repo.
3. Check the service logs for `StaticFiles` mount errors.
4. Hard-refresh the browser (`Ctrl+Shift+R` / `Cmd+Shift+R`) to clear cached assets.

### ❌ Render free-tier web service is slow to respond

**Cause**: Free-tier services spin down after 15 minutes of inactivity and take ~30 s to cold-start.

**Fix**: Visit the site URL — after the cold-start delay it will respond normally. Upgrade to a paid plan or use an external pinger service to keep it warm.

### ❌ Stripe payment errors (`No such price` / redirect loop)

**Cause**: `STRIPE_SECRET_KEY` or `STRIPE_PUBLISHABLE_KEY` is missing or set to the wrong key type.

**Fix**:
1. In the Render **Environment** tab, confirm both keys are set.
2. Use *test* keys (`sk_test_...` / `pk_test_...`) during development.
3. Set `APP_BASE_URL` to your Render service URL so Stripe can redirect back correctly.

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