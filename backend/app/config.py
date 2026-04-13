"""Minimal environment configuration for the backend."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Small settings object loaded directly from environment variables."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


settings = Settings()
