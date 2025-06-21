"""Basic watchdog to reset the bot after repeated alert failures."""


def reset_bot(reason: str) -> None:
    print(f"🔄 Reset triggered: {reason}")