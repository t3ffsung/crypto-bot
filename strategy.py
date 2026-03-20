import ta

def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['ma50'] = df['close'].rolling(window=50).mean()
    # We don't need the MA200 for the 1-minute stress test
    return df

def generate_signal(row):
    # STRESS TEST LOGIC: Buy any slight dip, sell any slight pump
    if row['rsi'] < 48: 
        return "BUY"
    elif row['rsi'] > 52:
        return "SELL"
    
    return "HOLD"
