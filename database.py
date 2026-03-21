import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

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
    """Fetches manual orders from React and deletes them from the queue."""
    try:
        db = firestore.client()
        orders_ref = db.collection('pending_orders')
        docs = orders_ref.stream()
        
        orders = []
        for doc in docs:
            order_data = doc.to_dict()
            orders.append(order_data)
            doc.reference.delete() # Delete it so we don't execute it twice!
            
        return orders
    except Exception as e:
        print(f"Queue Error: {e}")
        return []
