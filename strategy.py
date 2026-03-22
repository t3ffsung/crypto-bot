import ta
import pandas as pd

def apply_indicators(df):
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    
    adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx_ind.adx()
    
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd_diff'] = macd.macd_diff() 
    
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
        
    return df

def generate_signal(row):
    if pd.isna(row['adx']) or pd.isna(row['ema_21']): return "HOLD"
        
    # THE FIX: Lowered ADX from 25 to 20 so it catches emerging trends faster
    strong_trend = row['adx'] > 20
    
    bullish_trend = row['ema_9'] > row['ema_21']
    bearish_trend = row['ema_9'] < row['ema_21']
    
    # THE FIX: Widened RSI so it triggers on smaller pullbacks
    valid_rsi_long = 35 <= row['rsi'] <= 65 
    valid_rsi_short = 35 <= row['rsi'] <= 65
    
    macd_bullish = row['macd_diff'] > 0
    macd_bearish = row['macd_diff'] < 0
    
    not_touching_upper_band = row['close'] < row['bb_upper']
    not_touching_lower_band = row['close'] > row['bb_lower']
    
    if strong_trend and bullish_trend and valid_rsi_long and macd_bullish and not_touching_upper_band:
        return "BUY"
    elif strong_trend and bearish_trend and valid_rsi_short and macd_bearish and not_touching_lower_band:
        return "SELL"
        
    return "HOLD"
