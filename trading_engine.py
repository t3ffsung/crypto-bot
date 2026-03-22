from datetime import datetime

class TradingEngine:
    def __init__(self, saved_state=None):
        if saved_state:
            self.balance = float(saved_state.get('cash_balance', 3000.0))
            self.positions = saved_state.get('positions', {})
            print(f"🧠 Memory Loaded! Starting Cash: ${self.balance:.2f}")
        else:
            self.balance = 3000.0
            self.positions = {}
            print("🧠 Clean Slate. Starting Cash: $3000.00")
            
        self.trade_log = []
        self.bot_active = True

    def _calculate_amount(self, price, amount_usdt, amount_coin):
        if amount_usdt is None and amount_coin is None:
            amount_usdt = 100.0 
        if amount_coin:
            return float(amount_coin) * price, float(amount_coin)
        return float(amount_usdt), float(amount_usdt) / price

    def buy(self, symbol, price, amount_usdt=None, amount_coin=None, reason="Auto-Strategy"):
        if symbol in self.positions and self.positions[symbol]['type'] == 'SHORT':
            return self.close_position(symbol, price, reason="Buy to Cover Short")

        margin_usdt, coin_amount = self._calculate_amount(price, amount_usdt, amount_coin)
        fee = margin_usdt * 0.001 
        
        if self.balance < (margin_usdt + fee):
            print(f"⚠️ Insufficient margin for LONG on {symbol}.")
            return False

        self.balance -= (margin_usdt + fee)
        timestamp_str = datetime.now().isoformat()
        
        if symbol in self.positions:
            old_amount = self.positions[symbol]['amount']
            old_entry = self.positions[symbol]['entry_price']
            new_amount = old_amount + coin_amount
            new_entry = ((old_amount * old_entry) + (coin_amount * price)) / new_amount
            self.positions[symbol] = { 'type': 'LONG', 'amount': new_amount, 'entry_price': new_entry, 'timestamp': timestamp_str }
        else:
            self.positions[symbol] = { 'type': 'LONG', 'amount': coin_amount, 'entry_price': price, 'timestamp': timestamp_str }

        self.trade_log.append({ 'symbol': symbol, 'action': f'LONG ({reason})', 'price': price, 'amount': coin_amount, 'cost': margin_usdt, 'timestamp': timestamp_str })
        return True

    def sell(self, symbol, price, amount_usdt=None, amount_coin=None, reason="Auto-Strategy"):
        if symbol in self.positions and self.positions[symbol]['type'] == 'LONG':
            return self.close_position(symbol, price, reason="Sell to Close Long")

        margin_usdt, coin_amount = self._calculate_amount(price, amount_usdt, amount_coin)
        fee = margin_usdt * 0.001 
        
        if self.balance < (margin_usdt + fee):
            print(f"⚠️ Insufficient margin for SHORT on {symbol}.")
            return False

        self.balance -= (margin_usdt + fee) 
        timestamp_str = datetime.now().isoformat()
        
        if symbol in self.positions:
            old_amount = self.positions[symbol]['amount']
            old_entry = self.positions[symbol]['entry_price']
            new_amount = old_amount + coin_amount
            new_entry = ((old_amount * old_entry) + (coin_amount * price)) / new_amount
            self.positions[symbol] = { 'type': 'SHORT', 'amount': new_amount, 'entry_price': new_entry, 'timestamp': timestamp_str }
        else:
            self.positions[symbol] = { 'type': 'SHORT', 'amount': coin_amount, 'entry_price': price, 'timestamp': timestamp_str }

        self.trade_log.append({ 'symbol': symbol, 'action': f'SHORT ({reason})', 'price': price, 'amount': coin_amount, 'cost': margin_usdt, 'timestamp': timestamp_str })
        return True

    def close_position(self, symbol, current_price, reason="Liquidate"):
        if symbol not in self.positions: return False

        pos = self.positions.pop(symbol)
        pos_type = pos['type']
        coin_amount = pos['amount']
        entry_price = pos['entry_price']

        position_value = coin_amount * current_price
        margin_used = coin_amount * entry_price
        entry_fee = margin_used * 0.001
        exit_fee = position_value * 0.001

        if pos_type == 'LONG':
            gross_profit = position_value - margin_used
        else: 
            gross_profit = margin_used - position_value

        net_profit = gross_profit - entry_fee - exit_fee
        self.balance += (margin_used + gross_profit - exit_fee)
        
        self.trade_log.append({ 'symbol': symbol, 'action': f'CLOSE {pos_type} ({reason})', 'price': current_price, 'amount': coin_amount, 'profit': net_profit, 'timestamp': datetime.now().isoformat() })
        return True

    def check_stop_loss_and_take_profit(self, symbol, current_price):
        if symbol not in self.positions: return
        pos = self.positions[symbol]
        entry = pos['entry_price']
        
        # --- THE STRICT 1:2 RISK/REWARD SCALPING LOGIC ---
        if pos['type'] == 'LONG':
            if current_price <= entry * 0.99: # 1% Drop
                print(f"🛑 LONG STOP LOSS HIT: {symbol} (-1%)")
                self.close_position(symbol, current_price, reason="Stop Loss (1%)")
            elif current_price >= entry * 1.02: # 2% Pump
                print(f"🎯 LONG TAKE PROFIT HIT: {symbol} (+2%)")
                self.close_position(symbol, current_price, reason="Take Profit (2%)")
                
        elif pos['type'] == 'SHORT':
            if current_price >= entry * 1.01: # 1% Pump (Against the short)
                print(f"🛑 SHORT STOP LOSS HIT: {symbol} (-1%)")
                self.close_position(symbol, current_price, reason="Stop Loss (1%)")
            elif current_price <= entry * 0.98: # 2% Drop (In favor of the short)
                print(f"🎯 SHORT TAKE PROFIT HIT: {symbol} (+2%)")
                self.close_position(symbol, current_price, reason="Take Profit (2%)")

    def get_portfolio_value(self, current_prices):
        value = self.balance
        for symbol, pos in self.positions.items():
            current_price = current_prices.get(symbol, pos['entry_price'])
            margin_used = pos['amount'] * pos['entry_price']
            if pos['type'] == 'LONG':
                profit = (current_price - pos['entry_price']) * pos['amount']
            else:
                profit = (pos['entry_price'] - current_price) * pos['amount']
            value += (margin_used + profit)
        return value

    def check_circuit_breaker(self, current_value):
        if current_value < 2000.0: self.bot_active = False # Stop if we lose $1000 total
