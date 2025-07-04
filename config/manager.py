"""Unified configuration loader for environment variables and JSON file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

_CONFIG_PATH = Path(__file__).resolve().parent / "settings.json"
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

@lru_cache(maxsize=1)
def _load_config() -> dict[str, str]:
    data: dict[str, str] = {}
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH, override=False)
    return data


def get_config(key: str, fallback: str | None = None) -> str | None:
    """Returns a config value from env or settings.json with fallback."""
    data = _load_config()
    return os.getenv(key, data.get(key, fallback))

