"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-03 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # resource_types
    op.create_table(
        "resource_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_resource_types_id", "resource_types", ["id"], unique=False)

    # contracts
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type_id", sa.Integer(), nullable=False),
        sa.Column(
            "contract_kind",
            sa.Enum("REGULAR", "OPTION", "SMART", name="contractkind"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "OPEN", "ACCEPTED", "CLOSED", "CANCELLED", name="contractstatus"),
            nullable=False,
        ),
        sa.Column(
            "option_type",
            sa.Enum("CALL", "PUT", name="optiontype"),
            nullable=True,
        ),
        sa.Column("strike_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("premium", sa.Numeric(18, 6), nullable=True),
        sa.Column("expiration_at", sa.DateTime(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("delivery_location", sa.String(length=255), nullable=True),
        sa.Column("delivery_window_start", sa.DateTime(), nullable=True),
        sa.Column("delivery_window_end", sa.DateTime(), nullable=True),
        sa.Column("pricing_currency", sa.String(length=20), nullable=False),
        sa.Column("price_amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("chain", sa.String(length=80), nullable=True),
        sa.Column("contract_address", sa.String(length=255), nullable=True),
        sa.Column("seller_display_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["resource_type_id"], ["resource_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contracts_id", "contracts", ["id"], unique=False)

    # offers
    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("bidder_display_name", sa.String(length=120), nullable=False),
        sa.Column("offer_amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("offer_currency", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ACCEPTED", "REJECTED", "WITHDRAWN", name="offerstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offers_id", "offers", ["id"], unique=False)

    # payment_preferences
    op.create_table(
        "payment_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column(
            "method",
            sa.Enum("STRIPE", "CREDITS", "CRYPTO_WALLET", name="paymentmethod"),
            nullable=False,
        ),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_preferences_id", "payment_preferences", ["id"], unique=False)

    # Seed resource types
    op.bulk_insert(
        sa.table(
            "resource_types",
            sa.column("name", sa.String),
            sa.column("symbol", sa.String),
            sa.column("description", sa.String),
        ),
        [
            {"name": "Lunar Ice", "symbol": "LI", "description": "Water ice deposits found in permanently shadowed lunar craters"},
            {"name": "Helium-3", "symbol": "He3", "description": "Rare isotope mined from lunar regolith, valuable for fusion energy"},
            {"name": "Platinum Group Metals", "symbol": "PGM", "description": "Rare earth and platinum group metals from asteroid mining"},
            {"name": "Regolith", "symbol": "REG", "description": "Loose surface material covering solid rock on moons and asteroids"},
            {"name": "Iron-Nickel Ore", "symbol": "FeNi", "description": "Metallic asteroid composition used for in-situ manufacturing"},
            {"name": "Solar Energy Credits", "symbol": "SEC", "description": "Tokenised units of harvested solar energy in cislunar space"},
            {"name": "Carbonaceous Compounds", "symbol": "CC", "description": "Organic molecules and carbon compounds from C-type asteroids"},
        ],
    )


def downgrade() -> None:
    op.drop_table("payment_preferences")
    op.drop_table("offers")
    op.drop_table("contracts")
    op.drop_table("resource_types")
