import os
import time
import threading
from flask import Flask
from data import fetch_data
from strategy import apply_indicators, generate_signal
from trading_engine import TradingEngine
from database import update_portfolio_stats, log_trade_to_db, get_and_clear_pending_orders, load_portfolio_stats

app = Flask(__name__)

@app.route('/')
def home():
    return "Crypto Bot is Alive, Remembering, and Trading!"

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'PEPE/USDT']

saved_state = load_portfolio_stats()
trader = TradingEngine(saved_state)
last_trade_count = 0 

def run_bot_cycle():
    global last_trade_count
    if not trader.bot_active:
        return

    print(f"\n--- Checking Manual Queue ---")
    manual_orders = get_and_clear_pending_orders()
    for order in manual_orders:
        msymbol = order.get('symbol')
        maction = order.get('action')
        custom_amount = float(order.get('amount_usdt', 0))
        
        # THE FIX: Grab price straight from React. No API call to Binance needed!
        current_price = float(order.get('price', 0)) 
        
        try:
            if current_price > 0:
                if maction == "BUY" and msymbol not in trader.positions:
                    print(f"⚡ EXECUTING MANUAL BUY: {msymbol} for ${custom_amount}")
                    trader.buy(msymbol, current_price, amount_usdt=custom_amount, reason="Manual")
                elif maction == "SELL" and msymbol in trader.positions:
                    print(f"⚡ EXECUTING MANUAL SELL: {msymbol}")
                    trader.sell(msymbol, current_price, reason="Manual")
        except Exception as e:
            print(f"Manual Trade Failed: {e}")

    print(f"--- Fetching Market Data ---")
    current_prices = {}

    for symbol in SYMBOLS:
        try:
            df = fetch_data(symbol=symbol, timeframe='1m', limit=100)
            df = apply_indicators(df)
            latest_candle = df.iloc[-1]
            current_prices[symbol] = latest_candle['close']
            
            trader.check_stop_loss_and_take_profit(symbol, latest_candle['close'])
            signal = generate_signal(latest_candle)
            
            if signal == "BUY" and symbol not in trader.positions:
                trader.buy(symbol, latest_candle['close'])
                print(f"🟢 AUTO BUY {symbol}")
            elif signal == "SELL" and symbol in trader.positions:
                trader.sell(symbol, latest_candle['close'])
                print(f"🔴 AUTO SELL {symbol}")
        except Exception as e:
            pass

    portfolio_value = trader.get_portfolio_value(current_prices)
    trader.check_circuit_breaker(portfolio_value)

    try:
        update_portfolio_stats(trader.balance, portfolio_value, trader.positions)
        current_trade_count = len(trader.trade_log)
        
        if current_trade_count > last_trade_count:
            for i in range(last_trade_count, current_trade_count):
                log_trade_to_db(trader.trade_log[i])
            last_trade_count = current_trade_count
    except Exception as e:
         print(f"⚠️ Firebase Sync Error: {e}")

def run_bot_loop():
    time.sleep(5)
    while True:
        # THE FIX: The Immortal Thread. This prevents the bot from ever dying silently.
        try:
            run_bot_cycle()
        except Exception as e:
            print(f"🔥 FATAL BOT THREAD ERROR: {e} - Rebooting cycle...")
        
        time.sleep(60)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot_loop)
    bot_thread.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
