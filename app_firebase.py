
import pandas as pd
from decimal import Decimal
from datetime import datetime
from data_firebase import add_trade, add_mtm, add_pos, get_trades, get_mtm, get_positions
import plotly.express as px
import streamlit as st
from data_firebase import get_db




st.set_page_config(page_title="PNL Dashboard — Firebase", layout="wide")
st.title("PNL System ")

# Configuração da página
st.set_page_config(page_title="PNL Dashboard (Firebase)", layout="wide")

# --- Helpers ---
PRODUCTS = ["SoyBean", "SoyMeal", "YelCorn"]
CATEGORIES = ["FOB Vessel", "FOB Paper", "C&F Vessel"]
# Agora meses em vez de códigos
MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

def get_conversion_value(prod: str) -> Decimal:
    if prod == "SoyBean":
        return Decimal("36.7454")
    elif prod == "SoyMeal":
        return Decimal("1.1023")
    elif prod == "YelCorn":
        return Decimal("39.3678")
    else:
        return Decimal("1")

# --- UI ---
st.title("PNL System — Firebase Edition")

with st.sidebar:
    st.header("Controls")
    current_year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.now().year)
    prod_sidebar = st.selectbox("Product (quick select)", PRODUCTS)

    if "refresh_count" not in st.session_state:
        st.session_state["refresh_count"] = 0

    if st.button("Refresh / Rerun"):
        st.session_state["refresh_count"] += 1
        try:
            st.rerun()
        except Exception:
            st.warning("Não foi possível forçar um rerun automaticamente. Atualize a página manualmente.")

tabs = st.tabs(["Overview", "Insert Trade", "Insert MTM", "Trade Log", "Graphs"])

# --- Overview Tab ---
with tabs[0]:
    st.header("Overview")
    cols = st.columns(3)
    for i, prod in enumerate(PRODUCTS):
        with cols[i]:
            st.subheader(prod)
            with st.spinner("Loading data..."):
                try:
                    trades = pd.DataFrame(get_trades())
                    mtm_df = pd.DataFrame(get_mtm())
                    pos_df = pd.DataFrame(get_positions())
                except Exception as e:
                    st.error(f"Erro ao carregar dados: {e}")
                    trades, mtm_df, pos_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

            st.markdown("**Trades**")
            st.dataframe(trades)

            st.markdown("**MTM (Mark-to-Market)**")
            st.dataframe(mtm_df)

            st.markdown("**Positions**")
            st.dataframe(pos_df)

# --- Insert Trade Tab ---
with tabs[1]:
    st.header("Insert Trade")
    with st.form("trade_form"):
        prod = st.selectbox("Product", PRODUCTS, index=PRODUCTS.index(prod_sidebar))
        op = st.selectbox("Operation", ["Purchase", "Sale"])
        year = st.number_input("Year", min_value=2000, max_value=2100, value=current_year)
        ton = st.number_input("Tons", min_value=0.0, step=1.0, value=1.0)
        lvl_pct = st.number_input("Level (%)", min_value=0.0, max_value=100.0, value=100.0)
        categories = st.multiselect("Categories", CATEGORIES, default=CATEGORIES)
        months = st.multiselect("Months", MONTHS, default=["Jan", "Feb", "Mar"])
        submit_trade = st.form_submit_button("Insert Trade")

    if submit_trade:
        try:
            lvl = Decimal(str(lvl_pct)) / Decimal("100")
            ton_dec = Decimal(str(ton))
            conV = get_conversion_value(prod)
            inserted = 0
            for cat in categories:
                for month in months:
                    notion = conV * lvl * ton_dec
                    trade_data = {
                        "product": prod,
                        "category": cat,
                        "month": month,
                        "year": int(year),
                        "operation": op,
                        "tons": float(ton),
                        "level": float(lvl),
                        "notion": float(notion)
                    }
                    add_trade(trade_data)
                    add_pos({
                        "product": prod,
                        "category": cat,
                        "month": month,
                        "year": int(year),
                        "pos": float(ton) if op == "Purchase" else -float(ton)
                    })
                    inserted += 1
            st.success(f"{inserted} trade(s) inserido(s) com sucesso.")
        except Exception as e:
            st.error(f"Erro ao inserir trade: {e}")

# --- Insert MTM Tab ---
with tabs[2]:
    st.header("Insert MTM (Mark-to-Market)")
    with st.form("mtm_form"):
        prod_mtm = st.selectbox("Product", PRODUCTS)
        year_mtm = st.number_input("Year", min_value=2000, max_value=2100, value=current_year, key="year_mtm")
        mtm_pct = st.number_input("MTM Level (%)", min_value=-100.0, max_value=1000.0, value=0.0)
        categories_mtm = st.multiselect("Categories", CATEGORIES, default=CATEGORIES, key="cat_mtm")
        months_mtm = st.multiselect("Months", MONTHS, default=["Jan", "Feb", "Mar"], key="month_mtm")
        submit_mtm = st.form_submit_button("Insert MTM")

    if submit_mtm:
        try:
            mtm = Decimal(str(mtm_pct)) / Decimal("100")
            updated = 0
            for cat in categories_mtm:
                for month in months_mtm:
                    mtm_data = {
                        "product": prod_mtm,
                        "category": cat,
                        "month": month,
                        "year": int(year_mtm),
                        "mtm": float(mtm),
                        "pnl": float(mtm) * 1000
                    }
                    add_mtm(mtm_data)
                    updated += 1
            st.success(f"Inserido/atualizado MTM para {updated} entradas.")
        except Exception as e:
            st.error(f"Erro ao inserir MTM: {e}")

# --- Trade Log Tab ---
with tabs[3]:
    st.header("Trade Log")
    with st.spinner("Loading trade log..."):
        try:
            df_trades = pd.DataFrame(get_trades())
            st.dataframe(df_trades)
        except Exception as e:
            st.error(f"Erro ao carregar trade log: {e}")

# --- Graphs Tab ---
with tabs[4]:
    st.header("PNL Graphs")
    prod_for_graph = st.selectbox("Product for graph", PRODUCTS)
    with st.spinner("Loading PNL timeseries..."):
        try:
            df_graph = pd.DataFrame(get_mtm())
            if df_graph.empty:
                st.info("No PNL timeseries available.")
            else:
                df_graph["month"] = pd.Categorical(df_graph["month"], categories=MONTHS, ordered=True)
                df_graph = df_graph.sort_values("month")
                fig = px.line(
                    df_graph,
                    x="month",
                    y="pnl",
                    color="category",
                    markers=True,
                    title=f"PNL timeseries — {prod_for_graph}"
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {e}")

# --- Footer ---
st.markdown("---")
