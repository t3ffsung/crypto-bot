import ccxt
import pandas as pd

def fetch_data(symbol='BTC/USDT', timeframe='1m', limit=300):
    # THE FIX: Use CCXT's native 'hostname' override. 
    # This cleanly swaps the domain without breaking the /api/v3/ paths!
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'hostname': 'data-api.binance.vision' 
    })

    # Fetch the data
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(ohlcv, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df

if __name__ == "__main__":
    df = fetch_data()
    print(df.tail())
