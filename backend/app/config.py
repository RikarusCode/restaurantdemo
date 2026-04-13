"""Minimal environment configuration for the backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or None
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


class Settings:
    """Read-only accessor so the rest of the app imports a single object."""

    @property
    def openai_api_key(self) -> str | None:
        return OPENAI_API_KEY

    @property
    def openai_model(self) -> str:
        return OPENAI_MODEL


settings = Settings()
