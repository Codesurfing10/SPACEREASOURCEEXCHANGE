from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Contract, ContractKind, ContractStatus, Offer, OfferStatus
from app.schemas import ContractCreate, ContractOut, OfferOut

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("/", response_model=list[ContractOut])
def list_contracts(
    resource_type_id: Optional[int] = Query(None),
    contract_kind: Optional[ContractKind] = Query(None),
    status: Optional[ContractStatus] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Contract).options(joinedload(Contract.resource_type))
    if resource_type_id:
        q = q.filter(Contract.resource_type_id == resource_type_id)
    if contract_kind:
        q = q.filter(Contract.contract_kind == contract_kind)
    if status:
        q = q.filter(Contract.status == status)
    return q.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ContractOut, status_code=201)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    contract = Contract(**payload.model_dump())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    # reload with resource_type
    return (
        db.query(Contract)
        .options(joinedload(Contract.resource_type))
        .filter(Contract.id == contract.id)
        .first()
    )


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = (
        db.query(Contract)
        .options(joinedload(Contract.resource_type))
        .filter(Contract.id == contract_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.patch("/{contract_id}/status", response_model=ContractOut)
def update_contract_status(
    contract_id: int, status: ContractStatus, db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract.status = status
    db.commit()
    db.refresh(contract)
    return (
        db.query(Contract)
        .options(joinedload(Contract.resource_type))
        .filter(Contract.id == contract_id)
        .first()
    )


@router.get("/{contract_id}/offers", response_model=list[OfferOut])
def list_offers_for_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return (
        db.query(Offer)
        .filter(Offer.contract_id == contract_id)
        .order_by(Offer.created_at.desc())
        .all()
    )


@router.patch("/{contract_id}/offers/{offer_id}/accept", response_model=OfferOut)
def accept_offer(contract_id: int, offer_id: int, db: Session = Depends(get_db)):
    offer = (
        db.query(Offer)
        .filter(Offer.id == offer_id, Offer.contract_id == contract_id)
        .first()
    )
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    offer.status = OfferStatus.ACCEPTED
    # Close other pending offers and mark contract as accepted
    db.query(Offer).filter(
        Offer.contract_id == contract_id,
        Offer.id != offer_id,
        Offer.status == OfferStatus.PENDING,
    ).update({"status": OfferStatus.REJECTED})
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        contract.status = ContractStatus.ACCEPTED
    db.commit()
    db.refresh(offer)
    return offer
