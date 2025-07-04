"""Trade monitoring and logging."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Monitor:
    """Simple logger-based monitor."""

    def log(self, msg: str) -> None:
        logger.info(msg)

    def update(self, trade_id: int, result: dict) -> None:
        logger.info("Trade %s closed: %s", trade_id, result)
