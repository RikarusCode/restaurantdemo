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

RETELL_API_KEY: str | None = os.getenv("RETELL_API_KEY") or None
RETELL_FROM_NUMBER: str | None = os.getenv("RETELL_FROM_NUMBER") or None
RETELL_AGENT_ID: str | None = os.getenv("RETELL_AGENT_ID") or None
TABLECALL_DIAL_OVERRIDE: str | None = os.getenv("TABLECALL_DIAL_OVERRIDE") or None
RETELL_POLL_INTERVAL_SECONDS: float = float(os.getenv("RETELL_POLL_INTERVAL_SECONDS", "2"))
RETELL_CALL_MAX_WAIT_SECONDS: float = float(os.getenv("RETELL_CALL_MAX_WAIT_SECONDS", "180"))


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

    @property
    def retell_api_key(self) -> str | None:
        return RETELL_API_KEY

    @property
    def retell_from_number(self) -> str | None:
        return RETELL_FROM_NUMBER

    @property
    def retell_agent_id(self) -> str | None:
        return RETELL_AGENT_ID

    @property
    def tablecall_dial_override(self) -> str | None:
        return TABLECALL_DIAL_OVERRIDE

    @property
    def retell_poll_interval_seconds(self) -> float:
        return RETELL_POLL_INTERVAL_SECONDS

    @property
    def retell_call_max_wait_seconds(self) -> float:
        return RETELL_CALL_MAX_WAIT_SECONDS


settings = Settings()
