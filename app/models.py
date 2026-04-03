from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ContractKind(str, enum.Enum):
    REGULAR = "REGULAR"
    OPTION = "OPTION"
    SMART = "SMART"


class ContractStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class OptionType(str, enum.Enum):
    CALL = "CALL"
    PUT = "PUT"


class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class PaymentMethod(str, enum.Enum):
    STRIPE = "STRIPE"
    CREDITS = "CREDITS"
    CRYPTO_WALLET = "CRYPTO_WALLET"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ResourceType(Base):
    __tablename__ = "resource_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    contracts: Mapped[list["Contract"]] = relationship(
        "Contract", back_populates="resource_type"
    )


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    resource_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resource_types.id"), nullable=False
    )
    contract_kind: Mapped[ContractKind] = mapped_column(
        Enum(ContractKind), nullable=False, default=ContractKind.REGULAR
    )
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT
    )

    # Option fields (nullable for non-option contracts)
    option_type: Mapped[OptionType | None] = mapped_column(
        Enum(OptionType), nullable=True
    )
    strike_price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    premium: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    expiration_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Quantity / logistics
    quantity: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="kg")
    delivery_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_window_start: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    delivery_window_end: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Pricing
    pricing_currency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="USD"
    )
    price_amount: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)

    # Smart-contract metadata (optional)
    chain: Mapped[str | None] = mapped_column(String(80), nullable=True)
    contract_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Identity (no auth)
    seller_display_name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    resource_type: Mapped["ResourceType"] = relationship(
        "ResourceType", back_populates="contracts"
    )
    offers: Mapped[list["Offer"]] = relationship("Offer", back_populates="contract")
    payment_preferences: Mapped[list["PaymentPreference"]] = relationship(
        "PaymentPreference", back_populates="contract"
    )


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id"), nullable=False
    )
    bidder_display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    offer_amount: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    offer_currency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="USD"
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus), nullable=False, default=OfferStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    contract: Mapped["Contract"] = relationship("Contract", back_populates="offers")


class PaymentPreference(Base):
    __tablename__ = "payment_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id"), nullable=False
    )
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    contract: Mapped["Contract"] = relationship(
        "Contract", back_populates="payment_preferences"
    )
