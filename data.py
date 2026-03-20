import ccxt
import pandas as pd

def fetch_data(symbol='BTC/USDT', timeframe='5m', limit=500):
    exchange = ccxt.binance()

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(ohlcv, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df


if __name__ == "__main__":
    df = fetch_data()
    print(df.tail())