from datetime import datetime

class TradingEngine:
    def __init__(self, saved_state=None):
        if saved_state:
            self.balance = float(saved_state.get('cash_balance', 1000.0))
            self.positions = saved_state.get('positions', {})
            print(f"🧠 Memory Loaded! Starting Cash: ${self.balance:.2f}")
        else:
            self.balance = 1000.0
            self.positions = {}
            print("🧠 Clean Slate. Starting Cash: $1000.00")
            
        self.trade_log = []
        self.bot_active = True

    def buy(self, symbol, price, amount_usdt=None, reason="Strategy"):
        if amount_usdt is None:
            amount_usdt = self.balance * 0.10
            
        amount_usdt = float(amount_usdt) 
        
        if self.balance < amount_usdt:
            print(f"Insufficient funds for {symbol}.")
            return

        coin_amount = amount_usdt / price
        fee = amount_usdt * 0.001 
        total_cost = amount_usdt + fee

        self.balance -= total_cost
        
        timestamp_str = datetime.now().isoformat()
        
        self.positions[symbol] = {
            'amount': coin_amount,
            'entry_price': price,
            'timestamp': timestamp_str
        }

        # THE FIX: Added 'timestamp' key so React can render it!
        self.trade_log.append({
            'symbol': symbol,
            'action': f'BUY ({reason})',
            'price': price,
            'amount': coin_amount,
            'cost': total_cost,
            'timestamp': timestamp_str 
        })

    def sell(self, symbol, price, reason="Strategy"):
        if symbol not in self.positions:
            return

        position = self.positions.pop(symbol)
        coin_amount = position['amount']
        entry_price = position['entry_price']

        gross_revenue = coin_amount * price
        fee = gross_revenue * 0.001
        net_revenue = gross_revenue - fee

        self.balance += net_revenue
        profit = net_revenue - (coin_amount * entry_price)
        
        timestamp_str = datetime.now().isoformat()

        # THE FIX: Added 'timestamp' key so React can render it!
        self.trade_log.append({
            'symbol': symbol,
            'action': f'SELL ({reason})',
            'price': price,
            'amount': coin_amount,
            'profit': profit,
            'timestamp': timestamp_str 
        })

    def check_stop_loss_and_take_profit(self, symbol, current_price):
        if symbol in self.positions:
            entry_price = self.positions[symbol]['entry_price']
            
            if current_price <= entry_price * 0.95:
                print(f"🛑 STOP LOSS TRIGGERED for {symbol}")
                self.sell(symbol, current_price, reason="Stop Loss")
                
            elif current_price >= entry_price * 1.10:
                print(f"🎯 TAKE PROFIT TRIGGERED for {symbol}")
                self.sell(symbol, current_price, reason="Take Profit")

    def get_portfolio_value(self, current_prices):
        value = self.balance
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                value += pos['amount'] * current_prices[symbol]
            else:
                value += pos['amount'] * pos['entry_price']
        return value

    def check_circuit_breaker(self, current_value):
        if current_value < 800.0:
            self.bot_active = False
