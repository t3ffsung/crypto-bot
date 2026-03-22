import ccxt
import pandas as pd

def fetch_data(symbol='BTC/USDT', timeframe='1m', limit=300):
    # THE FIX: Bypassing the US Geo-Block by overriding CCXT's default routing
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'urls': {
            'api': {
                'public': 'https://data-api.binance.vision/api'
            }
        }
    })

    # Fetch the data using the unblocked Vision API
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(ohlcv, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df


if __name__ == "__main__":
    df = fetch_data()
    print(df.tail())
