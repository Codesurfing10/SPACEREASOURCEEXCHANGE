from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Contract, Offer, OfferStatus
from app.schemas import OfferCreate, OfferOut

router = APIRouter(prefix="/api/offers", tags=["offers"])


@router.post("/{contract_id}", response_model=OfferOut, status_code=201)
def create_offer(
    contract_id: int, payload: OfferCreate, db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    offer = Offer(contract_id=contract_id, **payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.patch("/{offer_id}/withdraw", response_model=OfferOut)
def withdraw_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Only PENDING offers can be withdrawn"
        )
    offer.status = OfferStatus.WITHDRAWN
    db.commit()
    db.refresh(offer)
    return offer
