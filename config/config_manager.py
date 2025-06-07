"""Configuration manager for environment variables and JSON config.

Expected values
----------------
- ``LIVE_MODE``: ``"true"`` enables live trading while any other value
  (including absence of the variable) keeps the application in dry-run
  mode.
"""

import json
import os
from dataclasses import dataclass

@dataclass
class ConfigurationManager:
    """Load configuration values with environment variable overrides."""

    live_mode: bool = False

    @classmethod
    def load(cls, path: str = "config/config.json") -> "ConfigurationManager":
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        live_str = os.getenv("LIVE_MODE", str(data.get("LIVE_MODE", "false")))
        return cls(live_mode=live_str.lower() == "true")

CONFIG = ConfigurationManager.load()