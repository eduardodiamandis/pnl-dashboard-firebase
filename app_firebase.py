import streamlit as st
import pandas as pd
from decimal import Decimal
from datetime import datetime
from data_firebase import (
    add_trade, add_mtm, add_pos, get_trades, get_mtm, get_positions,
    update_trade, delete_trade, get_position_summary, get_pnl_summary,
    get_unique_values, get_mtm_by_trade
)

# ---------------------------------------------
# Configuração da página
# ---------------------------------------------
st.set_page_config(page_title="PNL Dashboard", layout="wide")
st.title("PNL Dashboard — Streamlit + Firebase")

# ---------------------------------------------
# Helpers e constantes
# ---------------------------------------------
PRODUCTS = ["SoyBean", "SoyMeal", "YelCorn"]
CATEGORIES = ["FOB Vessel", "FOB Paper", "C&F Vessel"]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
OPERATIONS = ["Purchase", "Sale"]

# Conversão base usada no cálculo de notion
def get_conversion_value(prod: str) -> Decimal:
    if prod == "SoyBean":
        return Decimal("36.7454")
    elif prod == "SoyMeal":
        return Decimal("1.1023")
    elif prod == "YelCorn":
        return Decimal("39.3678")
    else:
        return Decimal("1")

# ---------------------------------------------
# Barra lateral
# ---------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Overview", "Insert Trade", "Insert MTM", "Trade Log", "Graphs"]
)

# ---------------------------------------------
# Overview
# ---------------------------------------------
if page == "Overview":
    st.header("Overview by Product")
    year = st.sidebar.number_input("Year", 2000, 2100, datetime.now().year)

    cols = st.columns(3)
    for i, prod in enumerate(PRODUCTS):
        with cols[i]:
            st.subheader(prod)
            with st.spinner("Loading Data..."):
                try:
                    trades = pd.DataFrame(get_trades({"prod": prod, "year": year}))
                    pnl = pd.DataFrame(get_pnl_summary({"prod": prod, "year": year}))
                    pos = pd.DataFrame(get_position_summary())
                except Exception as e:
                    st.error(f"Error loading data: {e}")
                    trades = pnl = pos = pd.DataFrame()

            st.markdown("**Trades**")
            st.dataframe(trades)

            st.markdown("**PNL**")
            st.dataframe(pnl)

            st.markdown("**Positions**")
            st.dataframe(pos)

# ---------------------------------------------
# Insert Trade
# ---------------------------------------------
elif page == "Insert Trade":
    st.header("Insert New Trade")
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            prod = st.selectbox("Product", PRODUCTS)
            cat = st.selectbox("Category", CATEGORIES)
            month = st.selectbox("Month", MONTHS)
            year = st.number_input("Year", 2000, 2100, datetime.now().year)
        with col2:
            op = st.selectbox("Operation", OPERATIONS)
            ton = st.number_input("Tons", 0.0, step=1.0, value=1.0)
            lvl = st.number_input("Level", min_value=0.0, step=0.01, value=100.0)
            notion = float(get_conversion_value(prod)) * float(ton) * float(lvl)

        submit = st.form_submit_button("Insert Trade")

    if submit:
        try:
            trade_id = add_trade(prod, cat, month, year, op, ton, lvl, notion)
            if trade_id:
                st.success(f"Trade successfully added! ID: {trade_id}")
        except Exception as e:
            st.error(f"Error adding trade: {e}")

# ---------------------------------------------
# Insert MTM
# ---------------------------------------------
elif page == "Insert MTM":
    st.header("Insert Mark-to-Market (MTM)")
    trades = get_trades({"status": "active"})
    if not trades:
        st.info("No active trades found.")
    else:
        trade_opt = {
            f"{t['prod']} ({t.get('month', t.get('ship', 'N/A'))}/{t['year']}) - {t['op']}": t['id']
            for t in trades
        }

        with st.form("mtm_form"):
            selected_trade = st.selectbox("Select Trade", list(trade_opt.keys()))
            mtm = st.number_input("MTM Value", step=0.01)
            pnl = st.number_input("PNL Value", step=0.01)
            submit = st.form_submit_button("Insert MTM")

        if submit:
            try:
                add_mtm(trade_opt[selected_trade], mtm, pnl)
            except Exception as e:
                st.error(f"Error inserting MTM: {e}")

# ---------------------------------------------
# Trade Log
# ---------------------------------------------
elif page == "Trade Log":
    st.header("Trade Log")
    trades = get_trades()
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df)
    else:
        st.info("No trades found.")

# ---------------------------------------------
# Graphs (PNL Visualization)
# ---------------------------------------------
elif page == "Graphs":
    st.header("PNL Graphs")
    prod = st.selectbox("Select Product", PRODUCTS)
    pnl_data = get_pnl_summary({"prod": prod})
    if pnl_data:
        df = pd.DataFrame(pnl_data)
        st.line_chart(df.set_index("year")[["total_pnl"]])
    else:
        st.info("No PNL data to display.")

st.markdown("---")
st.caption("PNL System — Streamlit + Firebase (month-based version)")
