import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

def get_db_client():
    return firestore.client()

def load_portfolio_stats():
    try:
        db = firestore.client()
        doc = db.collection('bot_stats').document('live_portfolio').get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"Error loading memory: {e}")
    return None

# Added total_fees_paid to the sync
def update_portfolio_stats(cash_balance, total_value, positions, lifetime_pnl=0.0, total_fees_paid=0.0):
    db = firestore.client()
    doc_ref = db.collection('bot_stats').document('live_portfolio')
    doc_ref.set({
        'cash_balance': cash_balance,
        'total_value': total_value,
        'positions': positions,
        'lifetime_pnl': lifetime_pnl,
        'total_fees_paid': total_fees_paid,
        'last_updated': firestore.SERVER_TIMESTAMP
    })

def log_trade_to_db(trade_record):
    db = firestore.client()
    db.collection('trade_history').add(trade_record)
