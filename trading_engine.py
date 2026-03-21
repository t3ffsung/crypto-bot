from datetime import datetime

class TradingEngine:
    def __init__(self, starting_balance=1000.0):
        self.balance = starting_balance
        self.positions = {}
        self.trade_log = []
        self.bot_active = True

    def buy(self, symbol, price, timestamp=None, amount_usdt=None):
        # If no custom amount is provided, default to 10% of portfolio
        if amount_usdt is None:
            amount_usdt = self.balance * 0.10
        
        if self.balance < amount_usdt:
            print(f"Insufficient funds for {symbol}. Needed: {amount_usdt}, Have: {self.balance}")
            return

        coin_amount = amount_usdt / price
        fee = amount_usdt * 0.001
        total_cost = amount_usdt + fee

        self.balance -= total_cost
        self.positions[symbol] = {
            'amount': coin_amount,
            'entry_price': price,
            'timestamp': timestamp or datetime.now().isoformat()
        }

        trade_record = {
            'symbol': symbol,
            'action': 'BUY',
            'price': price,
            'amount': coin_amount,
            'cost': total_cost,
            'fee': fee,
            'time': timestamp or datetime.now().isoformat()
        }
        self.trade_log.append(trade_record)

    def sell(self, symbol, price, timestamp=None):
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

        trade_record = {
            'symbol': symbol,
            'action': 'SELL',
            'price': price,
            'amount': coin_amount,
            'revenue': net_revenue,
            'fee': fee,
            'profit': profit,
            'time': timestamp or datetime.now().isoformat()
        }
        self.trade_log.append(trade_record)

    def check_stop_loss(self, symbol, current_price, timestamp=None):
        if symbol in self.positions:
            entry_price = self.positions[symbol]['entry_price']
            # 5% Stop Loss
            if current_price <= entry_price * 0.95:
                print(f"🛑 STOP LOSS TRIGGERED for {symbol}")
                self.sell(symbol, current_price, timestamp)

    def get_portfolio_value(self, current_prices):
        value = self.balance
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                value += pos['amount'] * current_prices[symbol]
            else:
                value += pos['amount'] * pos['entry_price']
        return value

    def check_circuit_breaker(self, current_value):
        # Pause if portfolio drops below $800
        if current_value < 800.0:
            self.bot_active = False
