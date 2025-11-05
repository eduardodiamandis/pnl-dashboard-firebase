import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional

# --- Inicialização segura do Firebase ---
if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()


# -------------------------------------------------
# Funções de Validação
# -------------------------------------------------
def validate_trade_data(prod: str, cat: str, month: str, year: int, ton: float, lvl: float, notion: float) -> List[str]:
    errors = []
    if not prod:
        errors.append("Product is required")
    if not cat:
        errors.append("Category is required")
    if not month:
        errors.append("Month is required")
    if year < 2000 or year > 2100:
        errors.append("Year must be between 2000 and 2100")
    if ton <= 0:
        errors.append("Ton must be greater than zero")
    if notion == 0:
        errors.append("Notion cannot be zero")
    return errors


# -------------------------------------------------
# Inserção de Dados
# -------------------------------------------------
def add_trade(prod: str, cat: str, month: str, year: int, op: str, ton: float, lvl: float, notion: float) -> Optional[str]:
    """Insere uma nova trade"""
    try:
        errors = validate_trade_data(prod, cat, month, year, ton, lvl, notion)
        if errors:
            for e in errors:
                st.error(e)
            return None

        doc_ref = db.collection("trades").document()
        data = {
            "prod": prod,
            "cat": cat,
            "month": month,
            "year": int(year),
            "op": op,
            "ton": float(ton),
            "lvl": float(lvl),
            "notion": float(notion),
            "status": "active",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        }
        doc_ref.set(data)
        return doc_ref.id
    except Exception as e:
        st.error(f"Erro ao adicionar trade: {e}")
        return None


def add_mtm(trade_id: str, mtm: float, pnl: float) -> bool:
    """Insere MTM e PNL vinculados a uma trade"""
    try:
        trade_ref = db.collection("trades").document(trade_id)
        trade_doc = trade_ref.get()
        if not trade_doc.exists:
            st.error("Trade não encontrada.")
            return False

        trade_data = trade_doc.to_dict()
        doc_ref = db.collection("mtm").document()
        doc_ref.set({
            "trade_id": trade_id,
            "prod": trade_data["prod"],
            "cat": trade_data["cat"],
            "month": trade_data["month"],
            "year": trade_data["year"],
            "mtm": float(mtm),
            "pnl": float(pnl),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar MTM: {e}")
        return False


def add_pos(prod: str, cat: str, month: str, year: int, pos: float) -> bool:
    """Adiciona ou atualiza posição"""
    try:
        doc_ref = db.collection("positions").document()
        doc_ref.set({
            "prod": prod,
            "cat": cat,
            "month": month,
            "year": int(year),
            "pos": float(pos),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reg": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar posição: {e}")
        return False


# -------------------------------------------------
# Leitura e Consultas
# -------------------------------------------------
def get_trades(filters: Optional[Dict] = None) -> List[Dict]:
    try:
        query = db.collection("trades")
        if filters:
            for key, val in filters.items():
                if val != "":
                    query = query.where(key, "==", val)
        docs = query.order_by("reg", direction=firestore.Query.DESCENDING).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Erro ao buscar trades: {e}")
        return []


def get_mtm(filters: Optional[Dict] = None) -> List[Dict]:
    try:
        query = db.collection("mtm")
        if filters:
            for key, val in filters.items():
                if val != "":
                    query = query.where(key, "==", val)
        docs = query.order_by("reg", direction=firestore.Query.DESCENDING).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Erro ao buscar MTM: {e}")
        return []


def get_positions(filters: Optional[Dict] = None) -> List[Dict]:
    try:
        query = db.collection("positions")
        if filters:
            for key, val in filters.items():
                if val != "":
                    query = query.where(key, "==", val)
        docs = query.order_by("reg", direction=firestore.Query.DESCENDING).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Erro ao buscar posições: {e}")
        return []


def get_mtm_by_trade(trade_id: str) -> List[Dict]:
    try:
        docs = db.collection("mtm").where("trade_id", "==", trade_id).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        st.error(f"Erro ao buscar MTM por trade: {e}")
        return []


# -------------------------------------------------
# Resumos e Agregações
# -------------------------------------------------
def get_position_summary() -> List[Dict]:
    try:
        trades = get_trades()
        summary = {}
        for t in trades:
            if t.get("status") != "active":
                continue
            key = f"{t['prod']}_{t['year']}"
            if key not in summary:
                summary[key] = {
                    "prod": t["prod"],
                    "year": t["year"],
                    "total_ton": 0,
                    "total_notion": 0,
                    "count": 0
                }
            summary[key]["total_ton"] += t["ton"]
            summary[key]["total_notion"] += t["notion"]
            summary[key]["count"] += 1
        return list(summary.values())
    except Exception as e:
        st.error(f"Erro ao calcular resumo de posições: {e}")
        return []


def get_pnl_summary() -> List[Dict]:
    try:
        mtms = get_mtm()
        summary = {}
        for m in mtms:
            key = f"{m['prod']}_{m['year']}"
            if key not in summary:
                summary[key] = {
                    "prod": m["prod"],
                    "year": m["year"],
                    "total_mtm": 0,
                    "total_pnl": 0,
                    "count": 0
                }
            summary[key]["total_mtm"] += m["mtm"]
            summary[key]["total_pnl"] += m["pnl"]
            summary[key]["count"] += 1
        return list(summary.values())
    except Exception as e:
        st.error(f"Erro ao calcular PNL: {e}")
        return []


def get_db():
    return db
