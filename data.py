import requests
import pandas as pd

def fetch_data(symbol='BTC/USDT', timeframe='1m', limit=300):
    # Binance API requires symbols without the slash (e.g., 'BTCUSDT')
    formatted_symbol = symbol.replace('/', '')
    
    # We directly hit the unblocked Vision API, bypassing CCXT entirely
    url = 'https://data-api.binance.vision/api/v3/klines'
    params = {
        'symbol': formatted_symbol,
        'interval': timeframe,
        'limit': limit
    }
    
    # Make the request
    response = requests.get(url, params=params)
    
    # If Binance gives us an error, print it loudly
    if response.status_code != 200:
        raise Exception(f"Binance API Error: {response.text}")
        
    data = response.json()
    
    # Binance returns a list of lists. We only need the first 6 columns.
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
    ])
    
    # Keep the essential columns and convert strings to floats
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.astype(float)
    
    # Convert timestamp to readable datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    return df

if __name__ == "__main__":
    df = fetch_data()
    print(df.tail())
