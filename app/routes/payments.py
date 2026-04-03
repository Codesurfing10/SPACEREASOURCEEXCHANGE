from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Contract, PaymentPreference
from app.schemas import PaymentPreferenceCreate, PaymentPreferenceOut, StripeSessionOut

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post(
    "/{contract_id}/preference",
    response_model=PaymentPreferenceOut,
    status_code=201,
)
def add_payment_preference(
    contract_id: int,
    payload: PaymentPreferenceCreate,
    db: Session = Depends(get_db),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    pref = PaymentPreference(
        contract_id=contract_id,
        method=payload.method,
        details=payload.details,
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


@router.get("/{contract_id}/preferences", response_model=list[PaymentPreferenceOut])
def list_payment_preferences(contract_id: int, db: Session = Depends(get_db)):
    return (
        db.query(PaymentPreference)
        .filter(PaymentPreference.contract_id == contract_id)
        .all()
    )


@router.post("/{contract_id}/stripe-session", response_model=StripeSessionOut)
def create_stripe_session(contract_id: int, db: Session = Depends(get_db)):
    """Create a Stripe Checkout Session for the contract's price."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Stripe is not configured. Set STRIPE_SECRET_KEY.",
        )
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    stripe.api_key = settings.stripe_secret_key

    # Amount in cents (USD) or smallest currency unit
    amount_cents = int(float(contract.price_amount) * 100)
    currency = (
        contract.pricing_currency.lower()
        if contract.pricing_currency.lower() in ("usd", "eur", "gbp")
        else "usd"
    )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": contract.title},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{settings.app_base_url}/contracts/{contract_id}?payment=success",
        cancel_url=f"{settings.app_base_url}/contracts/{contract_id}?payment=cancelled",
        metadata={"contract_id": str(contract_id)},
    )

    return StripeSessionOut(session_id=session.id, checkout_url=session.url)
