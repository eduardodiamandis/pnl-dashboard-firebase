import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional

# --- Secure Firebase Initialization ---
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------------------------------
# Validation Functions
# -------------------------------------------------
def validate_trade_data(prod: str, cat: str, ship: str, year: int, ton: float, lvl: float, notion: float) -> List[str]:
    """Validates input data for a trade"""
    errors = []
    
    if not prod or len(prod.strip()) == 0:
        errors.append("Product is required")
    if not cat or len(cat.strip()) == 0:
        errors.append("Category is required")
    if year < 2000 or year > 2100:
        errors.append("Year must be between 2000 and 2100")
    if ton <= 0:
        errors.append("Tonage must be greater than zero")
    if lvl < 0:
        errors.append("Level cannot be negative")
    if notion <= 0:
        errors.append("Notion must be greater than zero")
        
    return errors

# -------------------------------------------------
# Improved Insert Functions
# -------------------------------------------------
def add_trade(prod: str, cat: str, ship: str, year: int, op: str, ton: float, lvl: float, notion: float) -> Optional[str]:
    """Adds a new trade record and returns the created ID"""
    try:
        # Validation
        errors = validate_trade_data(prod, cat, ship, year, ton, lvl, notion)
        if errors:
            for error in errors:
                st.error(f"Validation error: {error}")
            return None
        
        doc_ref = db.collection("trades").document()
        trade_data = {
            "prod": prod.strip(),
            "cat": cat.strip(),
            "ship": ship.strip(),
            "year": int(year),
            "op": op.strip(),
            "ton": float(ton),
            "lvl": float(lvl),
            "notion": float(notion),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat(),
            "status": "active"
        }
        doc_ref.set(trade_data)
        st.success(f"Trade added successfully! ID: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        st.error(f"Error adding trade: {e}")
        return None

def add_mtm(trade_id: str, mtm: float, pnl: float) -> bool:
    """Adds MTM and PNL information referencing the trade"""
    try:
        # Check if trade exists
        trade_ref = db.collection("trades").document(trade_id)
        trade_doc = trade_ref.get()
        
        if not trade_doc.exists:
            st.error("Trade not found")
            return False
        
        trade_data = trade_doc.to_dict()
        
        doc_ref = db.collection("mtm").document()
        doc_ref.set({
            "trade_id": trade_id,
            "prod": trade_data["prod"],
            "cat": trade_data["cat"],
            "ship": trade_data["ship"],
            "year": trade_data["year"],
            "mtm": float(mtm),
            "pnl": float(pnl),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        st.success("MTM added successfully!")
        return True
    except Exception as e:
        st.error(f"Error adding MTM: {e}")
        return False

def add_pos(prod: str, cat: str, ship: str, year: int, pos: int) -> bool:
    """Adds or updates position by product/category"""
    try:
        if pos < 0:
            st.error("Position cannot be negative")
            return False
            
        doc_ref = db.collection("positions").document()
        doc_ref.set({
            "prod": prod.strip(),
            "cat": cat.strip(),
            "ship": ship.strip(),
            "year": int(year),
            "pos": int(pos),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        st.success("Position added successfully!")
        return True
    except Exception as e:
        st.error(f"Error adding position: {e}")
        return False

# -------------------------------------------------
# Read Functions with Advanced Filters
# -------------------------------------------------
def get_trades(filters: Optional[Dict] = None) -> List[Dict]:
    """Returns all registered trades with optional filters"""
    try:
        query = db.collection("trades")
        
        # Apply filters if provided
        if filters:
            if filters.get('prod'):
                query = query.where("prod", "==", filters['prod'].strip())
            if filters.get('year'):
                query = query.where("year", "==", int(filters['year']))
            if filters.get('cat'):
                query = query.where("cat", "==", filters['cat'].strip())
            if filters.get('ship'):
                query = query.where("ship", "==", filters['ship'].strip())
            if filters.get('status'):
                query = query.where("status", "==", filters['status'])
            if filters.get('date_start'):
                query = query.where("date", ">=", filters['date_start'])
            if filters.get('date_end'):
                query = query.where("date", "<=", filters['date_end'])
        
        # Order by registration date (newest first)
        query = query.order_by("reg", direction=firestore.Query.DESCENDING)
        
        docs = query.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error fetching trades: {e}")
        return []

def get_mtm(filters: Optional[Dict] = None) -> List[Dict]:
    """Filters MTM records with multiple criteria"""
    try:
        query = db.collection("mtm")
        
        if filters:
            if filters.get('trade_id'):
                query = query.where("trade_id", "==", filters['trade_id'])
            if filters.get('prod'):
                query = query.where("prod", "==", filters['prod'].strip())
            if filters.get('year'):
                query = query.where("year", "==", int(filters['year']))
            if filters.get('date_start'):
                query = query.where("date", ">=", filters['date_start'])
            if filters.get('date_end'):
                query = query.where("date", "<=", filters['date_end'])
        
        query = query.order_by("reg", direction=firestore.Query.DESCENDING)
        docs = query.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error fetching MTM: {e}")
        return []

def get_positions(filters: Optional[Dict] = None) -> List[Dict]:
    """Filters positions with multiple criteria"""
    try:
        query = db.collection("positions")
        
        if filters:
            if filters.get('prod'):
                query = query.where("prod", "==", filters['prod'].strip())
            if filters.get('year'):
                query = query.where("year", "==", int(filters['year']))
            if filters.get('cat'):
                query = query.where("cat", "==", filters['cat'].strip())
        
        query = query.order_by("reg", direction=firestore.Query.DESCENDING)
        docs = query.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error fetching positions: {e}")
        return []

# -------------------------------------------------
# Update and Delete Functions
# -------------------------------------------------
def update_trade(trade_id: str, **kwargs) -> bool:
    """Updates specific fields of a trade"""
    try:
        # Check if trade exists
        trade_ref = db.collection("trades").document(trade_id)
        if not trade_ref.get().exists:
            st.error("Trade not found")
            return False
        
        update_data = {}
        
        # Prepare data for update
        for key, value in kwargs.items():
            if value is not None:
                if key in ['year']:
                    update_data[key] = int(value)
                elif key in ['ton', 'lvl', 'notion']:
                    update_data[key] = float(value)
                elif key in ['prod', 'cat', 'ship', 'op']:
                    update_data[key] = value.strip()
                else:
                    update_data[key] = value
        
        trade_ref.update(update_data)
        st.success("Trade updated successfully!")
        return True
    except Exception as e:
        st.error(f"Error updating trade: {e}")
        return False

def delete_trade(trade_id: str) -> bool:
    """Deletes a trade (soft delete)"""
    try:
        trade_ref = db.collection("trades").document(trade_id)
        if not trade_ref.get().exists:
            st.error("Trade not found")
            return False
            
        trade_ref.update({"status": "inactive"})
        st.success("Trade deleted successfully!")
        return True
    except Exception as e:
        st.error(f"Error deleting trade: {e}")
        return False

def get_mtm_by_trade(trade_id: str) -> List[Dict]:
    """Gets all MTMs for a specific trade"""
    try:
        docs = db.collection("mtm").where("trade_id", "==", trade_id).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Error fetching trade MTM: {e}")
        return []

# -------------------------------------------------
# Aggregation and Summary Functions
# -------------------------------------------------
def get_position_summary() -> List[Dict]:
    """Returns aggregated position summary"""
    try:
        trades = get_trades()
        summary = {}
        
        for trade in trades:
            if trade.get('status') != 'active':
                continue
                
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
        st.error(f"Error calculating summary: {e}")
        return []

def get_pnl_summary(filters: Optional[Dict] = None) -> List[Dict]:
    """Returns PNL summary by product and year"""
    try:
        mtm_data = get_mtm(filters)
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

# -------------------------------------------------
# Utility Functions
# -------------------------------------------------
def get_unique_values(collection: str, field: str) -> List[str]:
    """Returns unique values for a specific field in a collection"""
    try:
        docs = db.collection(collection).stream()
        values = set()
        for doc in docs:
            data = doc.to_dict()
            if field in data and data[field]:
                values.add(data[field])
        return sorted(list(values))
    except Exception as e:
        st.error(f"Error getting unique values: {e}")
        return []

def get_db():
    """Returns Firestore database instance"""
    return db
