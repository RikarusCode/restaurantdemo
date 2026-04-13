"""Minimal environment configuration for the backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

K2_BASE_URL: str | None = os.getenv("K2_BASE_URL") or None
K2_API_KEY: str | None = os.getenv("K2_API_KEY") or None
K2_MODEL: str | None = os.getenv("K2_MODEL") or None

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or None
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


class Settings:
    """Read-only accessor so the rest of the app imports a single object."""

    @property
    def llm_api_key(self) -> str | None:
        return K2_API_KEY or OPENAI_API_KEY

    @property
    def llm_model(self) -> str:
        return K2_MODEL or OPENAI_MODEL

    @property
    def llm_base_url(self) -> str | None:
        return K2_BASE_URL

    @property
    def llm_provider(self) -> str:
        return "k2" if K2_API_KEY else "openai"

    @property
    def openai_api_key(self) -> str | None:
        """Backward-compatible accessor for older code paths."""

        return self.llm_api_key

    @property
    def openai_model(self) -> str:
        """Backward-compatible accessor for older code paths."""

        return self.llm_model


settings = Settings()
