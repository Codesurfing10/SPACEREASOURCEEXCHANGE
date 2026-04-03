from __future__ import annotations

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./space_exchange.db"
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    app_base_url: str = "http://localhost:8000"
    debug: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
