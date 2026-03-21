import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

def load_portfolio_stats():
    """Reads the last known portfolio state from the database on boot."""
    try:
        db = firestore.client()
        doc = db.collection('bot_stats').document('live_portfolio').get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"Error loading memory: {e}")
    return None

def update_portfolio_stats(cash_balance, total_value, positions):
    db = firestore.client()
    doc_ref = db.collection('bot_stats').document('live_portfolio')
    doc_ref.set({
        'cash_balance': cash_balance,
        'total_value': total_value,
        'positions': positions,
        'last_updated': firestore.SERVER_TIMESTAMP
    })

def log_trade_to_db(trade_record):
    db = firestore.client()
    db.collection('trade_history').add(trade_record)

def get_and_clear_pending_orders():
    try:
        db = firestore.client()
        orders_ref = db.collection('pending_orders')
        docs = orders_ref.stream()
        
        orders = []
        for doc in docs:
            orders.append(doc.to_dict())
            doc.reference.delete() 
        return orders
    except Exception as e:
        return []
