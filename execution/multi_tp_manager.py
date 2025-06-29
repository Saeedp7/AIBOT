from __future__ import annotations

import MetaTrader5 as mt5
from typing import Dict, List, Tuple

from utils.trade_journal import update_trade
from utils.logger import log_trade_action

# Track groups by a master ticket id
_groups: Dict[int, dict] = {}
_ticket_map: Dict[int, Tuple[int, int]] = {}


def register_group(
    tickets: List[int],
    symbol: str,
    direction: str,
    entry: float,
    sl: float,
    tp_levels: List[float],
    sl_buffer: float,
) -> int:
    """Register a new multi-TP order group."""
    if not tickets:
        return -1
    group_id = tickets[0]
    _groups[group_id] = {
        "tickets": tickets,
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "tp_levels": tp_levels,
        "sl_buffer": sl_buffer,
    }
    for idx, t in enumerate(tickets):
        _ticket_map[t] = (group_id, idx)
    return group_id


def _modify_sl(ticket: int, new_sl: float, reached: List[int]) -> None:
    """Send modify order request for SL update."""
    pos = mt5.positions_get(ticket=ticket)
    if not pos:
        return
    pos = pos[0]
    req = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": ticket,
        "sl": new_sl,
        "tp": pos.tp,
    }
    res = mt5.order_send(req)
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        update_trade(ticket, sl=new_sl, sl_moved=True, reached_tps=reached)
        log_trade_action(f"SL updated for {ticket} -> {new_sl}")


def handle_order_close(ticket: int, price: float) -> None:
    """Handle logic when a split order closes at TP or SL."""
    info = _ticket_map.pop(ticket, None)
    if not info:
        return
    group_id, idx = info
    data = _groups.get(group_id)
    if not data:
        return

    log_trade_action(f"TP{idx + 1} hit for ticket {ticket} @ {price}")
    update_trade(ticket, hit=f"TP{idx + 1}", result=f"TP{idx + 1}", exit_reason="target")

    remaining = [t for t in data["tickets"] if t != ticket and t in _ticket_map]
    entry = data["entry"]
    tp_levels = data["tp_levels"]
    sl_buffer = data.get("sl_buffer", 0.0)
    if idx == 0 and remaining:
        for t in remaining:
            _modify_sl(t, entry, [0])
    elif idx == 1 and remaining:
        # Only one ticket should remain
        buffer_adj = sl_buffer if data["direction"] == "buy" else -sl_buffer
        new_sl = tp_levels[1] - buffer_adj
        _modify_sl(remaining[0], new_sl, [0, 1])

    if not remaining:
        _groups.pop(group_id, None)