
import pandas as pd
from decimal import Decimal
from datetime import datetime
from data_firebase import add_trade, add_mtm, add_pos, get_trades, get_mtm, get_positions
import plotly.express as px
import streamlit as st
from data_firebase import get_db

db = get_db()
st.success("✅ Firebase conectado com sucesso!")


st.set_page_config(page_title="PNL Dashboard — Firebase", layout="wide")
st.title("PNL System ")

# --- constantes ---
PRODUCTS = ["SoyBean", "SoyMeal", "YelCorn"]
CATEGORIES = ["FOB Vessel", "FOB Paper", "C&F Vessel"]
SHIPMENTS = ["VSL", "PPR", "CNF"]

# --- barra lateral ---
with st.sidebar:
    st.header("Controls")
    current_year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.now().year)
    prod_sidebar = st.selectbox("Product (quick select)", PRODUCTS)
    if st.button("Refresh"):
        st.rerun()

# --- abas ---
tabs = st.tabs(["Overview", "Insert Trade", "Insert MTM", "Trade Log", "Graphs"])

# --- OVERVIEW ---
with tabs[0]:
    st.header("Overview")
    trades = pd.DataFrame(get_trades())
    mtm_df = pd.DataFrame(get_mtm())
    pos_df = pd.DataFrame(get_positions())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Trades")
        st.dataframe(trades)
    with col2:
        st.subheader("MTM")
        st.dataframe(mtm_df)
    with col3:
        st.subheader("Positions")
        st.dataframe(pos_df)

# --- INSERT TRADE ---
with tabs[1]:
    st.header("Insert Trade")
    with st.form("trade_form"):
        prod = st.selectbox("Product", PRODUCTS)
        op = st.selectbox("Operation", ["Purchase", "Sale"])
        year = st.number_input("Year", min_value=2000, max_value=2100, value=current_year)
        ton = st.number_input("Tons", min_value=0.0, step=1.0)
        lvl_pct = st.number_input("Level (%)", min_value=0.0, max_value=100.0)
        cat = st.selectbox("Category", CATEGORIES)
        ship = st.selectbox("Shipment", SHIPMENTS)
        submit_trade = st.form_submit_button("Insert Trade")

    if submit_trade:
        notion = Decimal(str(lvl_pct)) * Decimal(str(ton))
        add_trade(prod, cat, ship, int(year), op, ton, lvl_pct, float(notion))
        st.success(f"Trade for {prod} inserted successfully!")

# --- INSERT MTM ---
with tabs[2]:
    st.header("Insert MTM")
    with st.form("mtm_form"):
        trade_id = st.text_input("Trade ID")
        prod = st.selectbox("Product", PRODUCTS, key="mtm_prod")
        cat = st.selectbox("Category", CATEGORIES, key="mtm_cat")
        ship = st.selectbox("Shipment", SHIPMENTS, key="mtm_ship")
        year = st.number_input("Year", min_value=2000, max_value=2100, value=current_year, key="mtm_year")
        mtm_val = st.number_input("MTM Value", value=0.0)
        pnl_val = st.number_input("PnL Value", value=0.0)
        submit_mtm = st.form_submit_button("Insert MTM")
    if submit_mtm:
        add_mtm(trade_id, prod, cat, ship, int(year), float(mtm_val), float(pnl_val))
        st.success("MTM record added!")

# --- TRADE LOG ---
with tabs[3]:
    st.header("Trade Log")
    trades_df = pd.DataFrame(get_trades())
    if not trades_df.empty:
        st.dataframe(trades_df)
    else:
        st.info("No trades recorded yet.")

# --- GRAPHS ---
with tabs[4]:
    st.header("PNL Graphs")
    df_graph = pd.DataFrame(get_mtm())
    if df_graph.empty:
        st.info("No MTM data available yet.")
    else:
        df_graph["reg"] = pd.to_datetime(df_graph["reg"])
        fig = px.line(df_graph, x="reg", y="pnl", color="cat", title="PnL Over Time")
        st.plotly_chart(fig, use_container_width=True)
