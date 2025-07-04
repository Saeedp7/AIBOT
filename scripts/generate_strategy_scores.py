#!/usr/bin/env python
"""Generate initial strategy_scores.json for all strategies with regime-specific metrics."""

from __future__ import annotations

import argparse
import ast
import json
import os
from copy import deepcopy
from pathlib import Path

DEFAULT_OUTPUT = "ai_engine/strategy_scores.json"
REGIMES = ["unknown", "trending", "ranging", "volatile", "bullish", "bearish"]
DEFAULT_METRICS = {
    "win_rate": 0.0,
    "recent_score": 0.5,
    "regime_fit": 0.5,
}


def find_strategy_classes() -> list[str]:
    """Parse `strategies` package and return subclass names of `BaseStrategy`."""
    root = Path(__file__).resolve().parent.parent
    strategies_dir = root / "strategies"
    classes: list[str] = []

    for file in strategies_dir.glob("*.py"):
        if file.name in {"base.py", "strategy_selector.py"}:
            continue
        with open(file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (isinstance(base, ast.Name) and base.id == "BaseStrategy") or \
                       (isinstance(base, ast.Attribute) and base.attr == "BaseStrategy"):
                        classes.append(node.name)
                        break
    return classes


def build_scores() -> dict:
    """Return mapping of strategy names to nested regime metrics."""
    score_template = {regime: deepcopy(DEFAULT_METRICS) for regime in REGIMES}
    return {name: deepcopy(score_template) for name in find_strategy_classes()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate strategy_scores.json with regime breakdown")
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Do not overwrite existing output file",
    )
    parser.add_argument("-o", "--out", default=DEFAULT_OUTPUT, help="Output path")
    args = parser.parse_args()

    if args.skip_if_exists and os.path.exists(args.out):
        print(f"{args.out} already exists; skipping")
        return

    scores = build_scores()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
    print(f"Wrote scores for {len(scores)} strategies to {args.out}")


if __name__ == "__main__":
    main()
