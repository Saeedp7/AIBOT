# tests/meta_test_all_phases.py

import pytest
import sys

def run_test(module: str):
    print(f"\n🧪 Running: {module}")
    result = pytest.main([f"tests/{module}.py", "-v"])
    if result == 0:
        print(f"✅ {module} PASSED")
    else:
        print(f"❌ {module} FAILED")
    print("-" * 80)

def main():
    print("🔁 Starting Meta Test Suite for All Bot Phases")

    test_modules = [
        "test_phase4",          # Includes journaling, SL/TP logic
        "test_agents",          # Strategy score updates, selector logic
        "test_exposure_guard",  # Safe stacking logic
        "test_live_mode",       # Optional: real-time trade manager or scheduler loop
    ]

    failures = 0
    for mod in test_modules:
        result = pytest.main([f"tests/{mod}.py", "-v"])
        if result != 0:
            failures += 1

    if failures == 0:
        print("\n✅ ALL TEST MODULES PASSED")
    else:
        print(f"\n❌ {failures} MODULE(S) FAILED")

if __name__ == "__main__":
    main()
