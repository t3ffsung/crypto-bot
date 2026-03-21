import os
import time
import threading
from flask import Flask
from data import fetch_data
from strategy import apply_indicators, generate_signal
from trading_engine import TradingEngine
from database import update_portfolio_stats, log_trade_to_db, get_and_clear_pending_orders

# --- FLASK WEB SERVER SETUP ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Crypto Bot is Alive and Trading (STRESS TEST MODE)!"

# --- BOT LOGIC ---
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'PEPE/USDT']
trader = TradingEngine()
last_trade_count = 0 

def run_bot_cycle():
    global last_trade_count
    
    if not trader.bot_active:
        print("🚨 Circuit breaker active.")
        return

    print(f"\n--- Checking for Manual Commands ---")
    manual_orders = get_and_clear_pending_orders()
    for order in manual_orders:
        msymbol = order.get('symbol')
        maction = order.get('action')
        custom_amount = order.get('amount_usdt', 0)
        
        print(f"⚡ MANUAL OVERRIDE TRIGGERED: {maction} {msymbol} for ${custom_amount}")
        
        try:
            # We need the current price to execute manually
            m_df = fetch_data(symbol=msymbol, timeframe='1m', limit=2)
            current_price = m_df.iloc[-1]['close']
            
            if maction == "BUY" and msymbol not in trader.positions:
                trader.buy(msymbol, current_price, timestamp="MANUAL", amount_usdt=custom_amount)
            elif maction == "SELL" and msymbol in trader.positions:
                trader.sell(msymbol, current_price, timestamp="MANUAL")
        except Exception as e:
            print(f"Failed to execute manual trade: {e}")

    print(f"\n--- Fetching 1-minute market data ---")
    current_prices = {}

    for symbol in SYMBOLS:
        try:
            # FORCE 1-minute timeframe for rapid testing
            df = fetch_data(symbol=symbol, timeframe='1m', limit=100)
            df = apply_indicators(df)
            
            latest_candle = df.iloc[-1]
            current_prices[symbol] = latest_candle['close']
            timestamp = latest_candle['timestamp']
            
            trader.check_stop_loss(symbol, latest_candle['close'], timestamp=timestamp)
            signal = generate_signal(latest_candle)
            
            if signal == "BUY" and symbol not in trader.positions:
                trader.buy(symbol, latest_candle['close'], timestamp=timestamp)
                print(f"🟢 BUY {symbol}")
            elif signal == "SELL" and symbol in trader.positions:
                trader.sell(symbol, latest_candle['close'], timestamp=timestamp)
                print(f"🔴 SELL {symbol}")
                
        except Exception as e:
            # Print the error so we can see if Binance rate-limits us
            print(f"⚠️ Error with {symbol}: {e}")

    portfolio_value = trader.get_portfolio_value(current_prices)
    trader.check_circuit_breaker(portfolio_value)
    print(f"Total Value: ${portfolio_value:.2f}")

    # --- FIREBASE SYNC ---
    try:
        update_portfolio_stats(trader.balance, portfolio_value, trader.positions)
        current_trade_count = len(trader.trade_log)
        
        if current_trade_count > last_trade_count:
            for i in range(last_trade_count, current_trade_count):
                log_trade_to_db(trader.trade_log[i])
            last_trade_count = current_trade_count
    except Exception as e:
         print(f"⚠️ Firebase Error: {e}")

def run_bot_loop():
    """This keeps the bot running infinitely in the background."""
    time.sleep(10) # Give the web server a few seconds to boot up first
    while True:
        run_bot_cycle()
        # Sleep for exactly 60 seconds to match the 1-minute candles
        time.sleep(60)

if __name__ == "__main__":
    # 1. Start the bot logic in a background thread
    bot_thread = threading.Thread(target=run_bot_loop)
    bot_thread.start()
    
    # 2. Start the fake web server using Render's dynamic port
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
