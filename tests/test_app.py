"""
Smoke tests and basic endpoint tests for the Space Resource Exchange.
Uses an in-memory SQLite database for fast, isolated testing.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force SQLite for tests before importing the app
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_space.db")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# Test DB setup
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_space.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    # Seed resource types
    from app.models import ResourceType

    db = TestingSessionLocal()
    if db.query(ResourceType).count() == 0:
        db.add_all(
            [
                ResourceType(name="Lunar Ice", symbol="LI"),
                ResourceType(name="Helium-3", symbol="He3"),
            ]
        )
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)
    import os as _os
    try:
        _os.remove("test_space.db")
    except FileNotFoundError:
        pass


@pytest.fixture()
def client(setup_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_app_startup(client):
    """App should start and return 200 on the landing page."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Space Resource Exchange" in resp.text


def test_landing_page_contains_neon(client):
    """Landing page should contain neon-text class (space theme)."""
    resp = client.get("/")
    assert "neon-text" in resp.text


def test_browse_contracts_empty(client):
    """Browse contracts page should work with an empty DB."""
    resp = client.get("/contracts")
    assert resp.status_code == 200
    assert "Browse Contracts" in resp.text


def test_new_contract_form(client):
    """GET /contracts/new should render the create form."""
    resp = client.get("/contracts/new")
    assert resp.status_code == 200
    assert "Create a Contract" in resp.text or "New Contract" in resp.text


# ---------------------------------------------------------------------------
# API: ResourceType (via contracts list)
# ---------------------------------------------------------------------------


def test_api_list_contracts_empty(client):
    resp = client.get("/api/contracts/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# API: Contract CRUD
# ---------------------------------------------------------------------------


def test_create_contract_api(client):
    """POST /api/contracts/ should create a contract and return 201."""
    # First, get a resource type ID from the DB
    db = TestingSessionLocal()
    from app.models import ResourceType

    rt = db.query(ResourceType).first()
    db.close()
    assert rt is not None, "Seed data missing"

    payload = {
        "title": "Test Lunar Ice Contract",
        "description": "500 kg of lunar ice for sale",
        "resource_type_id": rt.id,
        "contract_kind": "REGULAR",
        "quantity": 500.0,
        "unit": "kg",
        "price_amount": 15000.0,
        "pricing_currency": "USD",
        "seller_display_name": "TestSeller",
    }
    resp = client.post("/api/contracts/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test Lunar Ice Contract"
    assert data["status"] == "OPEN"
    assert data["contract_kind"] == "REGULAR"


def test_get_contract_api(client):
    """GET /api/contracts/{id} should return the contract."""
    db = TestingSessionLocal()
    from app.models import Contract, ResourceType

    rt = db.query(ResourceType).first()
    # Create a contract directly
    c = Contract(
        title="He3 Option",
        resource_type_id=rt.id,
        contract_kind="OPTION",
        status="OPEN",
        quantity=100,
        unit="kg",
        price_amount=999.99,
        pricing_currency="USD",
        seller_display_name="OptSeller",
        option_type="CALL",
        strike_price=1200.0,
        premium=50.0,
    )
    db.add(c)
    db.commit()
    contract_id = c.id
    db.close()

    resp = client.get(f"/api/contracts/{contract_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == contract_id
    assert data["contract_kind"] == "OPTION"


def test_get_contract_404(client):
    resp = client.get("/api/contracts/99999")
    assert resp.status_code == 404


def test_contract_detail_page(client):
    """The HTML detail page should render for an existing contract."""
    db = TestingSessionLocal()
    from app.models import Contract, ResourceType

    rt = db.query(ResourceType).first()
    c = Contract(
        title="Smart Contract Test",
        resource_type_id=rt.id,
        contract_kind="SMART",
        status="OPEN",
        quantity=1,
        unit="unit",
        price_amount=100.0,
        pricing_currency="USDC",
        seller_display_name="SmartSeller",
        chain="Ethereum",
        contract_address="0xdeadbeef",
    )
    db.add(c)
    db.commit()
    contract_id = c.id
    db.close()

    resp = client.get(f"/contracts/{contract_id}")
    assert resp.status_code == 200
    assert "Smart Contract Test" in resp.text


# ---------------------------------------------------------------------------
# API: Offers
# ---------------------------------------------------------------------------


def test_create_and_list_offers(client):
    """POST /api/offers/{contract_id} then GET /api/contracts/{id}/offers."""
    db = TestingSessionLocal()
    from app.models import Contract, ResourceType

    rt = db.query(ResourceType).first()
    c = Contract(
        title="Offer Test Contract",
        resource_type_id=rt.id,
        contract_kind="REGULAR",
        status="OPEN",
        quantity=10,
        unit="ton",
        price_amount=5000.0,
        pricing_currency="USD",
        seller_display_name="OfferSeller",
    )
    db.add(c)
    db.commit()
    contract_id = c.id
    db.close()

    offer_payload = {
        "bidder_display_name": "BuyerOne",
        "offer_amount": 4800.0,
        "offer_currency": "USD",
        "message": "I'll take it!",
    }
    resp = client.post(f"/api/offers/{contract_id}", json=offer_payload)
    assert resp.status_code == 201, resp.text
    offer_data = resp.json()
    assert offer_data["status"] == "PENDING"

    # List offers
    resp2 = client.get(f"/api/contracts/{contract_id}/offers")
    assert resp2.status_code == 200
    offers = resp2.json()
    assert len(offers) >= 1
    assert offers[0]["bidder_display_name"] == "BuyerOne"


def test_accept_offer(client):
    """Accepting an offer should flip its status to ACCEPTED and contract to ACCEPTED."""
    db = TestingSessionLocal()
    from app.models import Contract, Offer, ResourceType

    rt = db.query(ResourceType).first()
    c = Contract(
        title="Accept Test",
        resource_type_id=rt.id,
        contract_kind="REGULAR",
        status="OPEN",
        quantity=5,
        unit="kg",
        price_amount=200.0,
        pricing_currency="USD",
        seller_display_name="AcceptSeller",
    )
    db.add(c)
    db.commit()

    offer = Offer(
        contract_id=c.id,
        bidder_display_name="Buyer2",
        offer_amount=195.0,
        offer_currency="USD",
        status="PENDING",
    )
    db.add(offer)
    db.commit()
    contract_id, offer_id = c.id, offer.id
    db.close()

    resp = client.patch(f"/api/contracts/{contract_id}/offers/{offer_id}/accept")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACCEPTED"

    # Contract should now be ACCEPTED
    resp2 = client.get(f"/api/contracts/{contract_id}")
    assert resp2.json()["status"] == "ACCEPTED"


# ---------------------------------------------------------------------------
# API: Payment preferences
# ---------------------------------------------------------------------------


def test_add_payment_preference(client):
    db = TestingSessionLocal()
    from app.models import Contract, ResourceType

    rt = db.query(ResourceType).first()
    c = Contract(
        title="Payment Pref Test",
        resource_type_id=rt.id,
        contract_kind="REGULAR",
        status="OPEN",
        quantity=1,
        unit="kg",
        price_amount=100.0,
        pricing_currency="USD",
        seller_display_name="PaySeller",
    )
    db.add(c)
    db.commit()
    contract_id = c.id
    db.close()

    pref_payload = {
        "method": "CRYPTO_WALLET",
        "details": {"wallet_address": "0xABC123"},
    }
    resp = client.post(f"/api/payments/{contract_id}/preference", json=pref_payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["method"] == "CRYPTO_WALLET"
    assert data["details"]["wallet_address"] == "0xABC123"


def test_stripe_session_no_key(client):
    """When STRIPE_SECRET_KEY is not set, endpoint should return 503."""
    from app.config import settings

    orig = settings.stripe_secret_key
    settings.stripe_secret_key = ""
    try:
        db = TestingSessionLocal()
        from app.models import Contract, ResourceType

        rt = db.query(ResourceType).first()
        c = Contract(
            title="Stripe Test",
            resource_type_id=rt.id,
            contract_kind="REGULAR",
            status="OPEN",
            quantity=1,
            unit="kg",
            price_amount=100.0,
            pricing_currency="USD",
            seller_display_name="StripeSeller",
        )
        db.add(c)
        db.commit()
        contract_id = c.id
        db.close()

        resp = client.post(f"/api/payments/{contract_id}/stripe-session")
        assert resp.status_code == 503
    finally:
        settings.stripe_secret_key = orig


# ---------------------------------------------------------------------------
# Form flow: create contract via HTML form
# ---------------------------------------------------------------------------


def test_create_contract_form_flow(client):
    db = TestingSessionLocal()
    from app.models import ResourceType

    rt = db.query(ResourceType).first()
    db.close()

    form_data = {
        "title": "Form Test Contract",
        "seller_display_name": "FormSeller",
        "resource_type_id": str(rt.id),
        "contract_kind": "REGULAR",
        "quantity": "100",
        "unit": "kg",
        "price_amount": "500",
        "pricing_currency": "USD",
    }
    resp = client.post("/contracts/new", data=form_data, follow_redirects=False)
    # Should redirect to the detail page
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/contracts/")

    # Follow the redirect
    detail_resp = client.get(location)
    assert detail_resp.status_code == 200
    assert "Form Test Contract" in detail_resp.text
