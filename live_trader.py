import os
import sys
import time
import threading
from flask import Flask
from data import fetch_data
from strategy import apply_indicators, generate_signal
from trading_engine import TradingEngine
from database import update_portfolio_stats, log_trade_to_db, load_portfolio_stats, get_db_client

app = Flask(__name__)
@app.route('/')
def home(): return "Quantum HFT Engine is Live!"

SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'SOL/USDT', 'DOT/USDT', 'MATIC/USDT', 'LTC/USDT',
    'LINK/USDT', 'BCH/USDT', 'TRX/USDT', 'XLM/USDT', 'ATOM/USDT', 'XMR/USDT', 'ETC/USDT', 'ALGO/USDT', 'VET/USDT', 'FIL/USDT',
    'PEPE/USDT', 'WIF/USDT', 'FLOKI/USDT', 'BONK/USDT', 'SHIB/USDT', 'AVAX/USDT', 'NEAR/USDT', 'RNDR/USDT', 'FET/USDT', 'INJ/USDT',
    'OP/USDT', 'ARB/USDT', 'SUI/USDT', 'APT/USDT', 'SEI/USDT', 'TIA/USDT', 'JUP/USDT', 'ORDI/USDT', 'RUNE/USDT', 'BOME/USDT'
]

MAX_OPEN_POSITIONS = 30
global_prices = {}

saved_state = load_portfolio_stats()
trader = TradingEngine(saved_state)
last_trade_count = 0 
trade_lock = threading.Lock()

def sync_to_firebase():
    global last_trade_count
    portfolio_value = trader.get_portfolio_value(global_prices)
    trader.check_circuit_breaker(portfolio_value)
    
    lifetime_pnl = trader.balance - 30000.0
    try:
        # Pass the total fees to the database
        update_portfolio_stats(trader.balance, portfolio_value, trader.positions, lifetime_pnl, trader.total_fees_paid)
        current_trade_count = len(trader.trade_log)
        if current_trade_count > last_trade_count:
            for i in range(last_trade_count, current_trade_count):
                log_trade_to_db(trader.trade_log[i])
            last_trade_count = current_trade_count
    except Exception as e:
         pass

def on_manual_order(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED':
            order = change.document.to_dict()
            msymbol = order.get('symbol')
            maction = order.get('action')
            amount_usdt = float(order.get('amount_usdt', 0))
            amount_coin = float(order.get('amount_coin', 0))
            current_price = float(order.get('price', 0))
            
            global_prices[msymbol] = current_price
            
            with trade_lock:
                if current_price > 0:
                    if maction == "CLOSE":
                        trader.close_position(msymbol, current_price, reason="Manual Liquidate")
                    elif maction == "BUY":
                        trader.buy(msymbol, current_price, amount_usdt=amount_usdt if amount_usdt else None, amount_coin=amount_coin if amount_coin else None, reason="Manual")
                    elif maction == "SELL":
                        trader.sell(msymbol, current_price, amount_usdt=amount_usdt if amount_usdt else None, amount_coin=amount_coin if amount_coin else None, reason="Manual")
                sync_to_firebase()
            change.document.reference.delete()

watch = get_db_client().collection('pending_orders').on_snapshot(on_manual_order)

def run_bot_cycle():
    if not trader.bot_active: return
    
    # --- THE SMART SCANNER ---
    symbols_to_scan = list(trader.positions.keys()) # Always monitor open trades
    can_open_new = trader.balance >= 1000.0 and len(trader.positions) < MAX_OPEN_POSITIONS
    
    if can_open_new:
        # We have margin. Add all other symbols to the scan list.
        for sym in SYMBOLS:
            if sym not in symbols_to_scan:
                symbols_to_scan.append(sym)
        print(f"\n[ ⏳ ] Full Scan Active ({len(symbols_to_scan)} assets). Open: {len(trader.positions)}/{MAX_OPEN_POSITIONS}")
    else:
        # We are broke or maxed out. Skip the heavy processing.
        print(f"\n[ 🛡️ ] Margin < $1000. Deep Scan Paused. Monitoring {len(symbols_to_scan)} open trades.")

    for symbol in symbols_to_scan:
        try:
            df = fetch_data(symbol=symbol, timeframe='1m', limit=300)
            df = apply_indicators(df)
            latest = df.iloc[-1]
            global_prices[symbol] = latest['close']
            
            with trade_lock:
                if symbol in trader.positions:
                    trader.check_stop_loss_and_take_profit(symbol, latest['close'])
                elif can_open_new: # Only look for signals if we have cash
                    signal = generate_signal(latest)
                    if signal == "BUY":
                        print(f"🤖 AUTO LONG {symbol} ($1000)")
                        trader.buy(symbol, latest['close'])
                        sync_to_firebase()
                    elif signal == "SELL":
                        print(f"🤖 AUTO SHORT {symbol} ($1000)")
                        trader.sell(symbol, latest['close'])
                        sync_to_firebase()
        except Exception as e:
            print(f"⚠️ Skipping {symbol} | Error: {e}")
            
    with trade_lock: sync_to_firebase()
    print(f"[ ✅ ] Cycle complete. Portfolio: ${trader.get_portfolio_value(global_prices):.2f}")

def run_bot_loop():
    time.sleep(5)
    while True:
        try: run_bot_cycle()
        except Exception as e: print(f"🔥 FATAL ERROR: {e}")
        time.sleep(60) 

if __name__ == "__main__":
    try:
        bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
        bot_thread.start()
        port = int(os.environ.get('PORT', 10000))
        app.run(host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN QUANTUM ENGINE...")
        os._exit(0)
