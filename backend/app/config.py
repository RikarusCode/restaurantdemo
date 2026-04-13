"""Minimal environment configuration for the backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

LAVA_API_BASE_URL: str | None = os.getenv("LAVA_API_BASE_URL") or None
LAVA_SECRET_KEY: str | None = os.getenv("LAVA_SECRET_KEY") or None
LAVA_MODEL: str | None = os.getenv("LAVA_MODEL") or None

K2_BASE_URL: str | None = os.getenv("K2_BASE_URL") or None
K2_API_KEY: str | None = os.getenv("K2_API_KEY") or None
K2_MODEL: str | None = os.getenv("K2_MODEL") or None

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or None
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


class Settings:
    """Read-only accessor so the rest of the app imports a single object."""

    @property
    def llm_api_key(self) -> str | None:
        return LAVA_SECRET_KEY or K2_API_KEY or OPENAI_API_KEY

    @property
    def llm_model(self) -> str:
        return LAVA_MODEL or K2_MODEL or OPENAI_MODEL

    @property
    def llm_base_url(self) -> str | None:
        return LAVA_API_BASE_URL or K2_BASE_URL

    @property
    def llm_provider(self) -> str:
        if LAVA_SECRET_KEY:
            return "lava"
        if K2_API_KEY:
            return "k2"
        return "openai"

    @property
    def openai_api_key(self) -> str | None:
        """Backward-compatible accessor for older code paths."""

        return self.llm_api_key

    @property
    def openai_model(self) -> str:
        """Backward-compatible accessor for older code paths."""

        return self.llm_model


settings = Settings()
