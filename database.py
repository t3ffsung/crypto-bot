import firebase_admin
from firebase_admin import credentials, firestore

# 1. Initialize the Firebase connection using your key
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)

# 2. Connect to the Firestore database
db = firestore.client()

def update_portfolio_stats(balance, portfolio_value, active_positions):
    """Overwrites the main dashboard document with the absolute latest numbers."""
    doc_ref = db.collection('bot_stats').document('live_portfolio')
    doc_ref.set({
        'cash_balance': round(balance, 2),
        'total_value': round(portfolio_value, 2),
        'positions': active_positions, # Pushes the whole dictionary of held coins
        'last_updated': firestore.SERVER_TIMESTAMP
    })
    print("☁️ Synced live stats to Firestore.")

def log_trade_to_db(trade_data):
    """Adds a new individual trade to the history collection."""
    # We use .add() so it creates a new unique document for every trade
    db.collection('trade_history').add({
        'time': trade_data['time'],
        'symbol': trade_data['symbol'],
        'action': trade_data['action'],
        'price': trade_data['price'],
        'profit': trade_data['profit'],
        'timestamp': firestore.SERVER_TIMESTAMP # Ensures perfect chronological sorting
    })
    print(f"☁️ Logged {trade_data['action']} trade to Firestore.")