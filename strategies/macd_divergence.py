import pandas_ta as ta

class MACDDivergenceStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 35:
            return

        macd = ta.macd(data['close'])
        data['macd'] = macd['MACD_12_26_9']
        data['macd_signal'] = macd['MACDs_12_26_9']

        if data['macd'].iloc[-2] < data['macd_signal'].iloc[-2] and data['macd'].iloc[-1] > data['macd_signal'].iloc[-1]:
            self.signal = 'buy'
        elif data['macd'].iloc[-2] > data['macd_signal'].iloc[-2] and data['macd'].iloc[-1] < data['macd_signal'].iloc[-1]:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'