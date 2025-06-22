from __future__ import annotations

import inspect
import importlib
import pkgutil
from pathlib import Path

from .base import BaseStrategy


def discover_strategies() -> list[BaseStrategy]:
    """Dynamically load and instantiate all strategy classes."""
    strategies: list[BaseStrategy] = []
    package_dir = Path(__file__).resolve().parent
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        name = module_info.name
        if name in {"base", "strategy_selector"}:
            continue
        module = importlib.import_module(f"{__name__}.{name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                strategies.append(obj())
    return strategies