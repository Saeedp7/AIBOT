import time
import logging
import MetaTrader5 as mt5

from config.manager import get_config
from execution.order_manager import execute_fake_order
from monitoring.alert_manager import alert_trade_opened
from utils.market_status import is_market_open
from utils.stop_level import enforce_min_stop_distance

MAGIC_NUMBER = int(get_config("MAGIC_NUMBER", 123456))

logger = logging.getLogger(__name__)


def is_valid_sl_tp(symbol: str, order_type: str, price: float, sl: float, tp: float) -> bool:
    """Validate SL/TP against broker stop levels."""
    info = mt5.symbol_info(symbol)
    if not info:
        return False
    stop_level = getattr(info, "trade_stops_level", getattr(info, "stops_level", 0)) * info.point

    if order_type == "buy":
        if sl >= price or tp <= price:
            return False
        if (price - sl) < stop_level or (tp - price) < stop_level:
            return False
    else:
        if sl <= price or tp >= price:
            return False
        if (sl - price) < stop_level or (price - tp) < stop_level:
            return False
    return True


def execute_trade(
    direction: str, symbol: str, lot: float, sl: float, tp: float, magic_offset: int = 0
) -> int | None:
    if not is_market_open(symbol):
        logger.warning(f"[SKIP] Market is closed for {symbol}, skipping trade.")
        return None
    info = mt5.symbol_info(symbol)
    if not info:
        logger.error(f"\u26a0\ufe0f Failed to fetch SymbolInfo for {symbol}")
        return None
    trade_mode = getattr(info, "trade_mode", None)
    if trade_mode in (0, 3):
        logger.warning(f"{symbol} not tradeable now (market closed or disabled)")
        return None

    price_tick = mt5.symbol_info_tick(symbol)
    if price_tick is None:
        logging.warning(f"No price data for {symbol}")
        return None

    entry_price = price_tick.ask if direction == "buy" else price_tick.bid

    if not is_valid_sl_tp(symbol, direction, entry_price, sl, tp):
        info = mt5.symbol_info(symbol)
        stop_level = info.trade_stops_level * info.point if info else 0
        print(f"[VALIDATION FAILED] {symbol} ({direction})")
        print(
            f"Entry={entry_price:.2f}, SL={sl:.2f}, TP={tp:.2f}, MinStop={stop_level:.2f}"
        )
        print(
            f"\u274c Invalid SL/TP for {symbol} - Order rejected due to broker stop limits."
        )
        return None

    sl, _, valid = enforce_min_stop_distance(symbol, entry_price, sl, tp, direction)
    if not valid:
        return None

    print(f"\U0001F4E4 Executing {direction.upper()} on {symbol} @ {entry_price:.2f}")
    print(f"    SL: {sl:.2f} | TP: {tp:.2f}")
    if get_config("LIVE_MODE", "false").lower() != "true":
        logger.debug(
            "[SIM MODE] %s %s lot=%.2f price=%.5f sl=%s tp=%s",
            direction,
            symbol,
            lot,
            entry_price,
            sl,
            tp,
        )
        execute_fake_order(direction, symbol, lot, entry_price, sl=sl, tp=tp)
        alert_trade_opened(symbol, "sim", direction, entry_price, sl, tp)
        return int(time.time())

    deal_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
    symbol_info = mt5.symbol_info(symbol)
    type_filling = mt5.ORDER_FILLING_IOC  # default fallback
    override = get_config("FILLING_MODE_OVERRIDES", {})
    if symbol in override:
        type_filling = int(override[symbol])
    elif symbol_info and hasattr(symbol_info, "filling_mode"):
        if symbol_info.filling_mode in (
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_RETURN,
        ):
            type_filling = symbol_info.filling_mode
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": deal_type,
        "price": entry_price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC_NUMBER + magic_offset,
        "comment": "AI Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }
    if tp and tp > 0:
        request["tp"] = tp
    info = mt5.symbol_info(symbol)
    if not info or info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
        logger.warning(f"{symbol} is not tradeable now (market closed or disabled)")
        return None
    logger.info(f"Sending order for {symbol}...")
    logger.debug("Order details: %s", request)
    result = mt5.order_send(request)
    logger.debug(
        "MT5 retcode=%s comment=%s", getattr(result, "retcode", None), getattr(result, "comment", "")
    )
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info("Trade executed: ticket %s", result.order)
        alert_trade_opened(symbol, "live", direction, entry_price, sl, tp)
        return result.order
    logger.error(
        "Trade failed: retcode=%s reason=%s response=%s",
        getattr(result, "retcode", None),
        getattr(result, "comment", ""),
        result,
    )
    return result
