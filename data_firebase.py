import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# inicializa firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def add_trade(prod, cat, ship, year, op, ton, lvl, notion):
    """Insere uma nova trade no Firestore."""
    doc_ref = db.collection("trades").document()
    doc_ref.set({
        "prod": prod,
        "cat": cat,
        "ship": ship,
        "year": year,
        "op": op,
        "ton": ton,
        "lvl": lvl,
        "notion": notion,
        "reg": datetime.now()
    })

def add_mtm(trade_id, prod, cat, ship, year, mtm, pnl):
    """Adiciona registro MTM."""
    doc_ref = db.collection("mtm").document()
    doc_ref.set({
        "trade_id": trade_id,
        "prod": prod,
        "cat": cat,
        "ship": ship,
        "year": year,
        "mtm": mtm,
        "pnl": pnl,
        "reg": datetime.now()
    })

def add_pos(prod, cat, ship, year, pos):
    """Adiciona posição."""
    doc_ref = db.collection("positions").document()
    doc_ref.set({
        "prod": prod,
        "cat": cat,
        "ship": ship,
        "year": year,
        "pos": pos,
        "reg": datetime.now()
    })

def get_trades():
    trades = db.collection("trades").stream()
    return [t.to_dict() | {"id": t.id} for t in trades]

def get_mtm():
    mtm = db.collection("mtm").stream()
    return [m.to_dict() for m in mtm]

def get_positions():
    pos = db.collection("positions").stream()
    return [p.to_dict() for p in pos]
