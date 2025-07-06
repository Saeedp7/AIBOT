import os
import importlib
from inspect import isclass
from pathlib import Path

from .base import BaseStrategy

def discover_strategies():
    strategy_dir = Path(__file__).parent
    strategies = []
    for file in os.listdir(strategy_dir):
        name, ext = os.path.splitext(file)
        if ext != ".py" or name in {"__init__", "base", "strategy_selector"}:
            continue
        
        module = importlib.import_module(f"strategies.{name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if (
                isclass(obj)
                and hasattr(obj, "generate_signal")
                and issubclass(obj, BaseStrategy)
                and obj is not BaseStrategy
            ):
                strategies.append(obj())

    return strategies
