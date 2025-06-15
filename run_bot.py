"""Unified entrypoint for AutoTrade AI Bot."""

from live.scheduler_loop import scheduler_loop, _parse_args


def main() -> None:
    args = _parse_args()
    scheduler_loop(args)


if __name__ == "__main__":
    main()
