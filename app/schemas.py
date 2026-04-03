from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models import (
    ContractKind,
    ContractStatus,
    OfferStatus,
    OptionType,
    PaymentMethod,
)


# ---------------------------------------------------------------------------
# ResourceType
# ---------------------------------------------------------------------------


class ResourceTypeOut(BaseModel):
    id: int
    name: str
    symbol: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------


class ContractCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type_id: int
    contract_kind: ContractKind = ContractKind.REGULAR
    status: ContractStatus = ContractStatus.OPEN

    # Option fields
    option_type: Optional[OptionType] = None
    strike_price: Optional[float] = None
    premium: Optional[float] = None
    expiration_at: Optional[datetime] = None

    # Quantity / logistics
    quantity: float
    unit: str = "kg"
    delivery_location: Optional[str] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None

    # Pricing
    pricing_currency: str = "USD"
    price_amount: float

    # Smart-contract metadata
    chain: Optional[str] = None
    contract_address: Optional[str] = None

    seller_display_name: str

    @field_validator("quantity", "price_amount")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be greater than zero")
        return v


class ContractOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    resource_type_id: int
    contract_kind: ContractKind
    status: ContractStatus
    option_type: Optional[OptionType] = None
    strike_price: Optional[float] = None
    premium: Optional[float] = None
    expiration_at: Optional[datetime] = None
    quantity: float
    unit: str
    delivery_location: Optional[str] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None
    pricing_currency: str
    price_amount: float
    chain: Optional[str] = None
    contract_address: Optional[str] = None
    seller_display_name: str
    created_at: datetime
    updated_at: datetime
    resource_type: Optional[ResourceTypeOut] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Offer
# ---------------------------------------------------------------------------


class OfferCreate(BaseModel):
    bidder_display_name: str
    offer_amount: float
    offer_currency: str = "USD"
    message: Optional[str] = None

    @field_validator("offer_amount")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be greater than zero")
        return v


class OfferOut(BaseModel):
    id: int
    contract_id: int
    bidder_display_name: str
    offer_amount: float
    offer_currency: str
    message: Optional[str] = None
    status: OfferStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------


class PaymentPreferenceCreate(BaseModel):
    method: PaymentMethod
    details: dict = {}


class PaymentPreferenceOut(BaseModel):
    id: int
    contract_id: int
    method: PaymentMethod
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class StripeSessionOut(BaseModel):
    session_id: str
    checkout_url: str
