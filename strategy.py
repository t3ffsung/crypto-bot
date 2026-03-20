import ta

def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma200'] = df['close'].rolling(window=200).mean()

    return df

def generate_signal(row):
    # BUY: Only if RSI is oversold AND we are in a macro uptrend (above MA200)
    if row['rsi'] < 35 and row['close'] > row['ma200']:
        return "BUY"
    
    # SELL: If RSI is overbought OR trend is breaking down (drops below MA50)
    elif row['rsi'] > 65 or row['close'] < row['ma50']:
        return "SELL"
    
    return "HOLD"