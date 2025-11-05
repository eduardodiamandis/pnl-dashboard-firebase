import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- Inicialização segura do Firebase ---
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])  # lê as credenciais do Streamlit Secrets
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()  # cria cliente Firestore

# -------------------------------------------------
# Funções de inserção
# -------------------------------------------------
def add_trade(prod, cat, ship, year, op, ton, lvl, notion):
    """Adiciona um novo registro de trade na coleção 'trades'."""
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
            "reg": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar trade: {e}")
        return False


def add_mtm(id_trade, prod, cat, ship, year, mtm, pnl):
    """Adiciona ou atualiza informações de MTM e PNL."""
    try:
        doc_ref = db.collection("mtm").document()
        doc_ref.set({
            "id_trade": id_trade,
            "prod": prod,
            "cat": cat,
            "ship": ship,
            "year": int(year),
            "mtm": float(mtm),
            "pnl": float(pnl),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar MTM: {e}")
        return False


def add_pos(prod, cat, ship, year, pos):
    """Adiciona ou atualiza posição (pos) por produto/categoria."""
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
        st.error(f"Erro ao adicionar posição: {e}")
        return False


# -------------------------------------------------
# Funções de leitura
# -------------------------------------------------
def get_trades():
    """Retorna todos os trades cadastrados."""
    try:
        docs = db.collection("trades").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Erro ao buscar trades: {e}")
        return []


def get_mtm(prod=None, year=None):
    """Filtra os registros de MTM por produto e ano, se fornecidos."""
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
        st.error(f"Erro ao buscar MTM: {e}")
        return []


def get_positions(prod=None, year=None):
    """Filtra posições por produto e ano."""
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
        st.error(f"Erro ao buscar posições: {e}")
        return []


# -------------------------------------------------
# Função auxiliar opcional
# -------------------------------------------------
def get_db():
    """Retorna a instância do banco Firestore (caso precise em outro arquivo)."""
    return db
