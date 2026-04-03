from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, SessionLocal
from app.routes import contracts, offers, pages, payments


def _seed_resource_types() -> None:
    """Insert default resource types if the table is empty."""
    from app.models import ResourceType

    db = SessionLocal()
    try:
        if db.query(ResourceType).count() == 0:
            seed = [
                ResourceType(
                    name="Lunar Ice",
                    symbol="LI",
                    description="Water ice deposits found in permanently shadowed lunar craters",
                ),
                ResourceType(
                    name="Helium-3",
                    symbol="He3",
                    description="Rare isotope mined from lunar regolith, valuable for fusion energy",
                ),
                ResourceType(
                    name="Platinum Group Metals",
                    symbol="PGM",
                    description="Rare earth and platinum group metals from asteroid mining",
                ),
                ResourceType(
                    name="Regolith",
                    symbol="REG",
                    description="Loose surface material covering solid rock on moons and asteroids",
                ),
                ResourceType(
                    name="Iron-Nickel Ore",
                    symbol="FeNi",
                    description="Metallic asteroid composition used for in-situ manufacturing",
                ),
                ResourceType(
                    name="Solar Energy Credits",
                    symbol="SEC",
                    description="Tokenised units of harvested solar energy in cislunar space",
                ),
                ResourceType(
                    name="Carbonaceous Compounds",
                    symbol="CC",
                    description="Organic molecules and carbon compounds from C-type asteroids",
                ),
            ]
            db.add_all(seed)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables for SQLite dev; Alembic handles Postgres in production
    Base.metadata.create_all(bind=engine)
    _seed_resource_types()
    yield


app = FastAPI(
    title="Space Resource Exchange",
    description="MVP contract exchange platform for space resources",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(contracts.router)
app.include_router(offers.router)
app.include_router(payments.router)
