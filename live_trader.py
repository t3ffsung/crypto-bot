import time
from data import fetch_data
from strategy import apply_indicators, generate_signal
from trading_engine import TradingEngine
from database import update_portfolio_stats, log_trade_to_db

# The list of coins your bot will monitor
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT']
trader = TradingEngine()

# We track this so the bot only pushes NEW trades to the database
last_trade_count = 0 

def run_bot_cycle():
    global last_trade_count
    
    if not trader.bot_active:
        print("🚨 Bot is inactive due to circuit breaker. Waiting for manual reset.")
        return

    print(f"\n--- Fetching market data for {len(SYMBOLS)} symbols ---")
    current_prices = {}

    for symbol in SYMBOLS:
        try:
            # 1. Check stop loss first
            trader.check_stop_loss(symbol, latest_candle['close'], timestamp=timestamp)
            
            # 2. Generate signal
            signal = generate_signal(latest_candle)
            
            # 3. Execute (UPDATED LOGIC)
            if signal == "BUY" and symbol not in trader.positions:
                trader.buy(symbol, latest_candle['close'], timestamp=timestamp)
                print(f"🟢 Executed BUY for {symbol} at ${latest_candle['close']}")
            
            elif signal == "SELL" and symbol in trader.positions:
                trader.sell(symbol, latest_candle['close'], timestamp=timestamp)
                print(f"🔴 Executed SELL for {symbol} at ${latest_candle['close']}")                
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    # Calculate global metrics
    portfolio_value = trader.get_portfolio_value(current_prices)
    trader.check_circuit_breaker(portfolio_value)
    
    print(f"Total Portfolio Value: ${portfolio_value:.2f} | Available Cash: ${trader.balance:.2f}")

    # --- FIREBASE SYNC ---
    try:
        # 1. Push the current balance and active positions
        update_portfolio_stats(trader.balance, portfolio_value, trader.positions)
        
        # 2. Check if any new trades happened during this cycle and push them
        current_trade_count = len(trader.trade_log)
        if current_trade_count > last_trade_count:
            for i in range(last_trade_count, current_trade_count):
                log_trade_to_db(trader.trade_log[i])
            last_trade_count = current_trade_count
            
    except Exception as e:
         print(f"⚠️ Failed to sync with Firestore: {e}")

if __name__ == "__main__":
    print("🚀 Starting Live Crypto Bot...")
    while True:
        run_bot_cycle()
        print("Waiting 5 minutes...\n")
        time.sleep(300)