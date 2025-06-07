import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / '.env'

@lru_cache(maxsize=1)
def _load_env() -> None:
    """Load environment variables from .env file once."""
    load_dotenv(dotenv_path=_ENV_PATH, override=False)

def get_config(key: str, default=None):
    """Retrieve configuration value from environment with optional default."""
    _load_env()
    return os.getenv(key, default)