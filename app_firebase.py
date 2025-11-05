import streamlit as st
import pandas as pd
from datetime import datetime
from data_firebase import (
    add_trade, add_mtm, add_pos,
    get_trades, get_mtm, get_positions,
    get_position_summary, get_pnl_summary,
    get_mtm_by_trade
)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
PRODUCTS = ["SoyBean", "SoyMeal", "YelCorn"]
CATEGORIES = ["FOB Vessel", "FOB Paper", "C&F Vessel"]
MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

def get_conversion_value(prod: str) -> float:
    if prod == "SoyBean":
        return 36.7454
    elif prod == "SoyMeal":
        return 1.1023
    elif prod == "YelCorn":
        return 39.3678
    else:
        return 1.0


# -------------------------------------------------
# Configuração inicial
# -------------------------------------------------
st.set_page_config(page_title="PNL Dashboard", layout="wide")
st.title("PNL System — Firebase Version")


# -------------------------------------------------
# Tabs
# -------------------------------------------------
tabs = st.tabs(["Overview", "Insert Trade", "Insert MTM", "Trade Log", "PNL Summary"])

# --- OVERVIEW ---
with tabs[0]:
    st.header("Overview")
    with st.spinner("Loading data..."):
        trades = get_trades()
        mtm = get_mtm()
        pos = get_positions()

    st.subheader("Trades")
    st.dataframe(pd.DataFrame(trades))

    st.subheader("MTM")
    st.dataframe(pd.DataFrame(mtm))

    st.subheader("Positions")
    st.dataframe(pd.DataFrame(pos))


# --- INSERT TRADE ---
with tabs[1]:
    st.header("Insert Trade")
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            prod = st.selectbox("Product", PRODUCTS)
            cat = st.selectbox("Category", CATEGORIES)
            month = st.selectbox("Month", MONTHS)
            year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.now().year)
        with col2:
            op = st.selectbox("Operation", ["Purchase", "Sale"])
            ton = st.number_input("Tons", min_value=0.0, step=1.0, value=1.0)
            lvl = st.number_input("Level", min_value=0.0, step=0.01)
            notion = st.number_input("Notion", step=0.01)

        submitted = st.form_submit_button("Add Trade")
        if submitted:
            try:
                trade_id = add_trade(prod, cat, month, int(year), op, ton, lvl, notion)
                if trade_id:
                    st.success(f"Trade {trade_id} added successfully.")
            except Exception as e:
                st.error(f"Erro ao inserir trade: {e}")


# --- INSERT MTM ---
with tabs[2]:
    st.header("Insert MTM")
    trades = get_trades({"status": "active"})
    if trades:
        trade_opt = {f"{t['prod']} ({t['month']}/{t['year']}) - {t['op']}": t['id'] for t in trades}
        with st.form("mtm_form"):
            selected = st.selectbox("Select Trade", list(trade_opt.keys()))
            mtm_val = st.number_input("MTM Value", step=0.01)
            pnl_val = st.number_input("PNL Value", step=0.01)
            submitted = st.form_submit_button("Add MTM")
            if submitted:
                add_mtm(trade_opt[selected], mtm_val, pnl_val)
    else:
        st.info("No active trades found.")


# --- TRADE LOG ---
with tabs[3]:
    st.header("Trade Log")
    trades = get_trades()
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df)
    else:
        st.info("No trades available.")


# --- PNL SUMMARY ---
with tabs[4]:
    st.header("PNL Summary")
    pnl = get_pnl_summary()
    if pnl:
        df = pd.DataFrame(pnl)
        st.dataframe(df)
    else:
        st.info("No PNL data found.")
