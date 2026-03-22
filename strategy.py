import ta
import pandas as pd

def apply_indicators(df):
    # 1. Trend Direction: EMAs
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    
    # 2. Trend Strength: ADX (Crucial for filtering out sideways chop)
    adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx_ind.adx()
    
    # 3. Momentum: RSI & MACD
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd_diff'] = macd.macd_diff() # Histogram
    
    # 4. Volatility: Bollinger Bands
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
        
    return df

def generate_signal(row):
    # Wait for all indicators to warm up (ADX needs about 28 candles)
    if pd.isna(row['adx']) or pd.isna(row['ema_21']): return "HOLD"
        
    # --- MULTI-INDICATOR CONFLUENCE LOGIC ---
    
    # 1. Is there a strong trend? (ADX > 25 means the market is actually moving)
    strong_trend = row['adx'] > 25
    
    # 2. Trend Direction
    bullish_trend = row['ema_9'] > row['ema_21']
    bearish_trend = row['ema_9'] < row['ema_21']
    
    # 3. Safe Momentum (Must not be overbought or oversold)
    valid_rsi_long = 40 <= row['rsi'] <= 60 
    valid_rsi_short = 40 <= row['rsi'] <= 60
    
    # 4. Sharp Entry Trigger
    macd_bullish = row['macd_diff'] > 0
    macd_bearish = row['macd_diff'] < 0
    
    # 5. Volatility Filter (Don't buy the exact top or short the exact bottom)
    not_touching_upper_band = row['close'] < row['bb_upper']
    not_touching_lower_band = row['close'] > row['bb_lower']
    
    # --- STRICT EXECUTION ---
    # It ONLY fires if all 5 indicators give the green light simultaneously.
    if strong_trend and bullish_trend and valid_rsi_long and macd_bullish and not_touching_upper_band:
        return "BUY"
    elif strong_trend and bearish_trend and valid_rsi_short and macd_bearish and not_touching_lower_band:
        return "SELL"
        
    return "HOLD"
