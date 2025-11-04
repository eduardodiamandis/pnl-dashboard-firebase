import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import streamlit as st

# --- Função que inicializa e retorna o banco ---
def get_db():
    # Evita reinicialização se já estiver ativo
    if not firebase_admin._apps:
        try:
            # Lê o bloco [firebase] do secrets.toml
            firebase_config = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            st.write("✅ Firebase inicializado com sucesso.")
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {e}")
            raise
    return firestore.client()

# --- Funções CRUD ---
def add_trade(prod, cat, ship, year, op, ton, lvl, notion):
    db = get_db()
    data = {
        "prod": prod,
        "cat": cat,
        "ship": ship,
        "year": int(year),
        "op": op,
        "ton": float(ton),
        "lvl": float(lvl),
        "notion": float(notion),
        "reg": datetime.utcnow()
    }
    db.collection("trades").add(data)

def add_mtm(trade_id, prod, cat, ship, year, mtm, pnl):
    db = get_db()
    data = {
        "trade_id": trade_id,
        "prod": prod,
        "cat": cat,
        "ship": ship,
        "year": int(year),
        "mtm": float(mtm),
        "pnl": float(pnl),
        "reg": datetime.utcnow()
    }
    db.collection("mtm").add(data)

def add_pos(prod, cat, ship, year, pos):
    db = get_db()
    data = {
        "prod": prod,
        "cat": cat,
        "ship": ship,
        "year": int(year),
        "pos": float(pos),
        "reg": datetime.utcnow()
    }
    db.collection("positions").add(data)

def get_trades():
    db = get_db()
    docs = db.collection("trades").order_by("reg", direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]

def get_mtm():
    db = get_db()
    docs = db.collection("mtm").order_by("reg", direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]

def get_positions():
    db = get_db()
    docs = db.collection("positions").order_by("reg", direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict() for doc in docs]
