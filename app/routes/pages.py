from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    Contract,
    ContractKind,
    ContractStatus,
    Offer,
    OfferStatus,
    PaymentPreference,
    ResourceType,
)

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def landing(request: Request, db: Session = Depends(get_db)):
    total_contracts = db.query(Contract).count()
    open_contracts = (
        db.query(Contract).filter(Contract.status == ContractStatus.OPEN).count()
    )
    resource_types = db.query(ResourceType).all()
    recent = (
        db.query(Contract)
        .options(joinedload(Contract.resource_type))
        .filter(Contract.status == ContractStatus.OPEN)
        .order_by(Contract.created_at.desc())
        .limit(6)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "total_contracts": total_contracts,
            "open_contracts": open_contracts,
            "resource_types": resource_types,
            "recent_contracts": recent,
        },
    )


@router.get("/contracts", response_class=HTMLResponse)
def browse_contracts(
    request: Request,
    resource_type_id: Optional[int] = Query(None),
    contract_kind: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Contract).options(joinedload(Contract.resource_type))
    if resource_type_id:
        q = q.filter(Contract.resource_type_id == resource_type_id)
    if contract_kind:
        try:
            kind = ContractKind(contract_kind)
            q = q.filter(Contract.contract_kind == kind)
        except ValueError:
            pass
    if status:
        try:
            st = ContractStatus(status)
            q = q.filter(Contract.status == st)
        except ValueError:
            pass
    contracts = q.order_by(Contract.created_at.desc()).all()
    resource_types = db.query(ResourceType).all()
    return templates.TemplateResponse(
        request,
        "contracts/list.html",
        {
            "contracts": contracts,
            "resource_types": resource_types,
            "contract_kinds": list(ContractKind),
            "contract_statuses": list(ContractStatus),
            "selected_resource_type_id": resource_type_id,
            "selected_kind": contract_kind,
            "selected_status": status,
        },
    )


@router.get("/contracts/new", response_class=HTMLResponse)
def new_contract_form(request: Request, db: Session = Depends(get_db)):
    resource_types = db.query(ResourceType).all()
    return templates.TemplateResponse(
        request,
        "contracts/create.html",
        {
            "resource_types": resource_types,
            "contract_kinds": list(ContractKind),
            "currencies": ["USD", "CREDITS", "USDC", "ETH", "BTC"],
            "units": ["kg", "ton", "g", "oz", "unit"],
        },
    )


@router.post("/contracts/new", response_class=HTMLResponse)
def create_contract_form(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    resource_type_id: int = Form(...),
    contract_kind: str = Form(...),
    seller_display_name: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form("kg"),
    delivery_location: Optional[str] = Form(None),
    pricing_currency: str = Form("USD"),
    price_amount: float = Form(...),
    # option fields
    option_type: Optional[str] = Form(None),
    strike_price: Optional[float] = Form(None),
    premium: Optional[float] = Form(None),
    expiration_at: Optional[str] = Form(None),
    # smart contract fields
    chain: Optional[str] = Form(None),
    contract_address: Optional[str] = Form(None),
    # payment method
    payment_method: Optional[str] = Form(None),
    wallet_address: Optional[str] = Form(None),
    credits_handle: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    from datetime import datetime

    errors = []
    if quantity <= 0:
        errors.append("Quantity must be positive.")
    if price_amount <= 0:
        errors.append("Price must be positive.")

    if errors:
        resource_types = db.query(ResourceType).all()
        return templates.TemplateResponse(
            request,
            "contracts/create.html",
            {
                "errors": errors,
                "resource_types": resource_types,
                "contract_kinds": list(ContractKind),
                "currencies": ["USD", "CREDITS", "USDC", "ETH", "BTC"],
                "units": ["kg", "ton", "g", "oz", "unit"],
            },
            status_code=422,
        )

    exp = None
    if expiration_at:
        try:
            exp = datetime.fromisoformat(expiration_at)
        except ValueError:
            exp = None

    contract = Contract(
        title=title,
        description=description,
        resource_type_id=resource_type_id,
        contract_kind=ContractKind(contract_kind),
        status=ContractStatus.OPEN,
        seller_display_name=seller_display_name,
        quantity=quantity,
        unit=unit,
        delivery_location=delivery_location,
        pricing_currency=pricing_currency,
        price_amount=price_amount,
        option_type=option_type if option_type else None,
        strike_price=strike_price,
        premium=premium,
        expiration_at=exp,
        chain=chain,
        contract_address=contract_address,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # Record payment preference
    if payment_method:
        details: dict = {}
        if payment_method == "CRYPTO_WALLET" and wallet_address:
            details = {"wallet_address": wallet_address}
        elif payment_method == "CREDITS" and credits_handle:
            details = {"credits_handle": credits_handle}
        pref = PaymentPreference(
            contract_id=contract.id,
            method=payment_method,
            details=details,
        )
        db.add(pref)
        db.commit()

    return RedirectResponse(url=f"/contracts/{contract.id}", status_code=303)


@router.get("/contracts/{contract_id}", response_class=HTMLResponse)
def contract_detail(
    request: Request, contract_id: int, db: Session = Depends(get_db)
):
    contract = (
        db.query(Contract)
        .options(
            joinedload(Contract.resource_type),
            joinedload(Contract.offers),
            joinedload(Contract.payment_preferences),
        )
        .filter(Contract.id == contract_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    offers = (
        db.query(Offer)
        .filter(Offer.contract_id == contract_id)
        .order_by(Offer.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "contracts/detail.html",
        {
            "contract": contract,
            "offers": offers,
            "OfferStatus": OfferStatus,
            "ContractStatus": ContractStatus,
            "stripe_pk": __import__("app.config", fromlist=["settings"]).settings.stripe_publishable_key,
        },
    )


@router.post("/contracts/{contract_id}/offers", response_class=HTMLResponse)
def submit_offer(
    request: Request,
    contract_id: int,
    bidder_display_name: str = Form(...),
    offer_amount: float = Form(...),
    offer_currency: str = Form("USD"),
    message: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    errors = []
    if offer_amount <= 0:
        errors.append("Offer amount must be positive.")
    if not bidder_display_name.strip():
        errors.append("Display name is required.")

    if errors:
        offers = (
            db.query(Offer)
            .filter(Offer.contract_id == contract_id)
            .order_by(Offer.created_at.desc())
            .all()
        )
        from app.config import settings as cfg

        return templates.TemplateResponse(
            request,
            "contracts/detail.html",
            {
                "contract": contract,
                "offers": offers,
                "errors": errors,
                "OfferStatus": OfferStatus,
                "ContractStatus": ContractStatus,
                "stripe_pk": cfg.stripe_publishable_key,
            },
            status_code=422,
        )

    offer = Offer(
        contract_id=contract_id,
        bidder_display_name=bidder_display_name,
        offer_amount=offer_amount,
        offer_currency=offer_currency,
        message=message,
        status=OfferStatus.PENDING,
    )
    db.add(offer)
    db.commit()
    return RedirectResponse(url=f"/contracts/{contract_id}", status_code=303)


@router.post("/contracts/{contract_id}/accept-offer/{offer_id}")
def accept_offer_page(
    contract_id: int, offer_id: int, db: Session = Depends(get_db)
):
    offer = (
        db.query(Offer)
        .filter(Offer.id == offer_id, Offer.contract_id == contract_id)
        .first()
    )
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    offer.status = OfferStatus.ACCEPTED
    db.query(Offer).filter(
        Offer.contract_id == contract_id,
        Offer.id != offer_id,
        Offer.status == OfferStatus.PENDING,
    ).update({"status": OfferStatus.REJECTED})
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        contract.status = ContractStatus.ACCEPTED
    db.commit()
    return RedirectResponse(url=f"/contracts/{contract_id}", status_code=303)


@router.post("/contracts/{contract_id}/close")
def close_contract_page(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract.status = ContractStatus.CLOSED
    db.commit()
    return RedirectResponse(url=f"/contracts/{contract_id}", status_code=303)


@router.post("/contracts/{contract_id}/cancel")
def cancel_contract_page(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract.status = ContractStatus.CANCELLED
    db.commit()
    return RedirectResponse(url=f"/contracts/{contract_id}", status_code=303)
