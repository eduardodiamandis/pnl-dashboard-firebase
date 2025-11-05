import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- Secure Firebase Initialization ---
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------------------------------
# Insert Functions
# -------------------------------------------------
def add_trade(prod, cat, ship, year, op, ton, lvl, notion):
    """Adds a new trade record to the 'trades' collection."""
    try:
        doc_ref = db.collection("trades").document()
        doc_ref.set({
            "prod": prod,
            "cat": cat,
            "ship": ship,
            "year": int(year),
            "op": op,
            "ton": float(ton),
            "lvl": float(lvl),
            "notion": float(notion),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat(),
            "status": "active"
        })
        return doc_ref.id
    except Exception as e:
        st.error(f"Error adding trade: {e}")
        return None

def add_mtm(trade_id, mtm, pnl):
    """Adds or updates MTM and PNL information."""
    try:
        doc_ref = db.collection("mtm").document()
        doc_ref.set({
            "id_trade": trade_id,
            "mtm": float(mtm),
            "pnl": float(pnl),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Error adding MTM: {e}")
        return False

def add_pos(prod, cat, ship, year, pos):
    """Adds or updates position by product/category."""
    try:
        doc_ref = db.collection("positions").document()
        doc_ref.set({
            "prod": prod,
            "cat": cat,
            "ship": ship,
            "year": int(year),
            "pos": int(pos),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Error adding position: {e}")
        return False

# -------------------------------------------------
# Read Functions
# -------------------------------------------------
def get_trades(filters=None):
    """Returns all registered trades."""
    try:
        query = db.collection("trades")
        
        if filters:
            if filters.get('prod'):
                query = query.where("prod", "==", filters['prod'])
            if filters.get('year'):
                query = query.where("year", "==", int(filters['year']))
            if filters.get('status'):
                query = query.where("status", "==", filters['status'])
        
        docs = query.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error fetching trades: {e}")
        return []

def get_mtm(prod=None, year=None):
    """Filters MTM records by product and year if provided."""
    try:
        col = db.collection("mtm")
        query = col
        if prod:
            query = query.where("prod", "==", prod)
        if year:
            query = query.where("year", "==", int(year))
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Error fetching MTM: {e}")
        return []

def get_positions(prod=None, year=None):
    """Filters positions by product and year."""
    try:
        col = db.collection("positions")
        query = col
        if prod:
            query = query.where("prod", "==", prod)
        if year:
            query = query.where("year", "==", int(year))
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Error fetching positions: {e}")
        return []

# -------------------------------------------------
# Additional functions needed for app_firebase.py
# -------------------------------------------------
def update_trade(trade_id, **kwargs):
    """Updates specific fields of a trade."""
    try:
        doc_ref = db.collection("trades").document(trade_id)
        update_data = {}
        
        for key, value in kwargs.items():
            if value is not None:
                if key in ['year']:
                    update_data[key] = int(value)
                elif key in ['ton', 'lvl', 'notion']:
                    update_data[key] = float(value)
                else:
                    update_data[key] = value
        
        doc_ref.update(update_data)
        return True
    except Exception as e:
        st.error(f"Error updating trade: {e}")
        return False

def delete_trade(trade_id):
    """Deletes a trade (soft delete)."""
    try:
        doc_ref = db.collection("trades").document(trade_id)
        doc_ref.update({"status": "inactive"})
        return True
    except Exception as e:
        st.error(f"Error deleting trade: {e}")
        return False

def get_mtm_by_trade(trade_id):
    """Gets all MTMs for a specific trade."""
    try:
        docs = db.collection("mtm").where("id_trade", "==", trade_id).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Error fetching trade MTM: {e}")
        return []

def get_position_summary():
    """Returns an aggregated summary of positions."""
    try:
        trades = get_trades({"status": "active"})
        summary = {}
        
        for trade in trades:
            key = f"{trade['prod']}_{trade['year']}"
            if key not in summary:
                summary[key] = {
                    'prod': trade['prod'],
                    'year': trade['year'],
                    'total_ton': 0,
                    'total_notion': 0,
                    'trades_count': 0
                }
            
            summary[key]['total_ton'] += trade['ton']
            summary[key]['total_notion'] += trade['notion']
            summary[key]['trades_count'] += 1
            
        return list(summary.values())
    except Exception as e:
        st.error(f"Error calculating position summary: {e}")
        return []

def get_pnl_summary(filters=None):
    """Returns a PNL summary by product and year."""
    try:
        mtm_data = get_mtm(
            filters.get('prod') if filters else None, 
            filters.get('year') if filters else None
        )
        summary = {}
        
        for mtm in mtm_data:
            key = f"{mtm['prod']}_{mtm['year']}"
            if key not in summary:
                summary[key] = {
                    'prod': mtm['prod'],
                    'year': mtm['year'],
                    'total_mtm': 0,
                    'total_pnl': 0,
                    'records_count': 0
                }
            
            summary[key]['total_mtm'] += mtm['mtm']
            summary[key]['total_pnl'] += mtm['pnl']
            summary[key]['records_count'] += 1
            
        return list(summary.values())
    except Exception as e:
        st.error(f"Error calculating PNL summary: {e}")
        return []

def get_unique_values(collection, field):
    """Returns unique values for a field in a collection."""
    try:
        docs = db.collection(collection).stream()
        values = set()
        for doc in docs:
            data = doc.to_dict()
            if field in data:
                values.add(data[field])
        return sorted(list(values))
    except Exception as e:
        st.error(f"Error fetching unique values: {e}")
        return []

def get_db():
    """Returns the Firestore database instance."""
    return db
