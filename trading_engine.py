class TradingEngine:
    def __init__(self, initial_balance=1000, fee_rate=0.001):
        self.balance = initial_balance
        # Dictionary to hold multiple coins: {'BTC/USDT': {'amount': 0.05, 'entry_price': 60000}}
        self.positions = {} 
        self.fee_rate = fee_rate
        self.trade_log = []
        self.bot_active = True  # The circuit breaker switch

    def buy(self, symbol, price, timestamp=""):
        if not self.bot_active:
            return

        # Allocate 25% of available cash per trade to allow up to 4 concurrent positions
        trade_amount = self.balance * 0.25 
        
        # Don't buy if we already hold this coin, and ensure we have enough cash left
        if symbol not in self.positions and trade_amount > 10:
            fee = trade_amount * self.fee_rate
            usable_cash = trade_amount - fee
            
            coin_amount = usable_cash / price
            
            self.positions[symbol] = {'amount': coin_amount, 'entry_price': price}
            self.balance -= trade_amount
            
            self.trade_log.append({
                "time": str(timestamp), "symbol": symbol, "action": "BUY", 
                "price": price, "profit": None
            })

    def sell(self, symbol, price, timestamp=""):
        if symbol in self.positions:
            position = self.positions[symbol]
            gross_revenue = position['amount'] * price
            fee = gross_revenue * self.fee_rate
            net_revenue = gross_revenue - fee
            
            profit = net_revenue - (position['amount'] * position['entry_price'])
            self.balance += net_revenue
            
            self.trade_log.append({
                "time": str(timestamp), "symbol": symbol, "action": "SELL", 
                "price": price, "profit": round(profit, 2)
            })
            
            del self.positions[symbol]

    def check_stop_loss(self, symbol, price, timestamp="", stop_loss_pct=0.02):
        if symbol in self.positions:
            entry = self.positions[symbol]['entry_price']
            if price < entry * (1 - stop_loss_pct):
                self.sell(symbol, price, timestamp)
                self.trade_log[-1]["action"] = "STOP LOSS"

    def get_portfolio_value(self, current_prices):
        """Calculates total value of cash + all held coins."""
        total_value = self.balance
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                gross = position['amount'] * current_prices[symbol]
                fee = gross * self.fee_rate
                total_value += (gross - fee)
        return total_value

    def check_circuit_breaker(self, current_portfolio_value):
        """Halts all future buying if the total portfolio value drops below $100."""
        if current_portfolio_value < 100 and self.bot_active:
            self.bot_active = False
            self.trade_log.append({
                "time": "NOW", "symbol": "ALL", "action": "CIRCUIT BREAKER TRIGGERED", 
                "price": 0, "profit": 0
            })