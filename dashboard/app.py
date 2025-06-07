import os
import json
from flask import Flask, render_template, request

app = Flask(__name__)

TRADE_HISTORY = os.path.join('logs', 'trade_history.json')
SCORES_FILE = os.path.join('ai_engine', 'strategy_scores.json')
LOG_FILE = os.path.join('logs', 'trade_actions.log')


def _load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def _load_logs(path, lines=50):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return f.readlines()[-lines:]


def _get_open_trades(history):
    open_states = {'open', 'TP1 hit', 'TP2 hit'}
    return [t for t in history if t.get('result') in open_states]


@app.route('/', methods=['GET'])
def dashboard():
    symbol = request.args.get('symbol')
    history = _load_json(TRADE_HISTORY)
    scores = _load_json(SCORES_FILE)
    logs = _load_logs(LOG_FILE, lines=100)

    open_trades = _get_open_trades(history)

    if symbol:
        history = [h for h in history if h.get('symbol') == symbol]
        open_trades = [t for t in open_trades if t.get('symbol') == symbol]

    return render_template(
        'dashboard.html',
        open_trades=open_trades,
        history=history,
        scores=scores,
        logs=logs,
        symbol=symbol,
    )


if __name__ == '__main__':
    print("🚀 Launching Flask Dashboard on http://127.0.0.1:5000/")
    app.run(debug=True)
