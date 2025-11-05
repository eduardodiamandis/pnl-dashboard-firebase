import streamlit as st
import pandas as pd
from datetime import datetime
from data_firebase import (
    add_trade, add_mtm, add_pos, get_trades, get_mtm, get_positions,
    update_trade, delete_trade, get_position_summary, get_pnl_summary,
    get_unique_values, get_mtm_by_trade
)

# Page configuration
st.set_page_config(page_title="Trading System", page_icon="📊", layout="wide")

# Title
st.title("📊 Trading Management System")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Select Page",
    ["Add Trade", "View Trades", "Add MTM", "View MTM", "Position Summary", "PNL Summary"]
)

# Add Trade Page
if page == "Add Trade":
    st.header("Add New Trade")
    
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            prod = st.text_input("Product*")
            cat = st.text_input("Category*")
            ship = st.text_input("Ship")
            year = st.number_input("Year*", min_value=2000, max_value=2100, value=datetime.now().year)
        
        with col2:
            op = st.text_input("Operation")
            ton = st.number_input("Tonage*", min_value=0.1, format="%.2f")
            lvl = st.number_input("Level", min_value=0.0, format="%.2f")
            notion = st.number_input("Notion*", min_value=0.1, format="%.2f")
        
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            trade_id = add_trade(prod, cat, ship, year, op, ton, lvl, notion)
            if trade_id:
                st.success(f"Trade added with ID: {trade_id}")

# View Trades Page
elif page == "View Trades":
    st.header("View Trades")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_prod = st.selectbox("Filter by Product", [""] + get_unique_values("trades", "prod"))
    with col2:
        filter_year = st.selectbox("Filter by Year", [""] + get_unique_values("trades", "year"))
    with col3:
        filter_status = st.selectbox("Filter by Status", ["", "active", "inactive"])
    
    # Apply filters
    filters = {}
    if filter_prod:
        filters['prod'] = filter_prod
    if filter_year:
        filters['year'] = int(filter_year)
    if filter_status:
        filters['status'] = filter_status
    
    # Get and display trades
    trades = get_trades(filters)
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df)
        
        # Trade actions
        selected_trade = st.selectbox("Select trade for actions", [f"{t['id']} - {t['prod']}" for t in trades])
        if selected_trade:
            trade_id = selected_trade.split(" - ")[0]
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View MTM History"):
                    mtm_data = get_mtm_by_trade(trade_id)
                    if mtm_data:
                        st.dataframe(pd.DataFrame(mtm_data))
                    else:
                        st.info("No MTM records found for this trade")
            
            with col2:
                if st.button("Delete Trade"):
                    if delete_trade(trade_id):
                        st.rerun()
    else:
        st.info("No trades found with the selected filters")

# Add MTM Page
elif page == "Add MTM":
    st.header("Add MTM/PNL")
    
    # Get active trades for selection
    trades = get_trades({"status": "active"})
    if trades:
        trade_options = {f"{t['id']} - {t['prod']}": t['id'] for t in trades}
        
        with st.form("mtm_form"):
            selected_trade = st.selectbox("Select Trade*", list(trade_options.keys()))
            mtm_value = st.number_input("MTM Value*", format="%.2f")
            pnl_value = st.number_input("PNL Value*", format="%.2f")
            
            submitted = st.form_submit_button("Add MTM")
            if submitted:
                trade_id = trade_options[selected_trade]
                if add_mtm(trade_id, mtm_value, pnl_value):
                    st.success("MTM record added successfully")
    else:
        st.info("No active trades found. Please add a trade first.")

# View MTM Page
elif page == "View MTM":
    st.header("View MTM Records")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        mtm_filter_prod = st.selectbox("Filter by Product", [""] + get_unique_values("mtm", "prod"), key="mtm_prod")
    with col2:
        mtm_filter_year = st.selectbox("Filter by Year", [""] + get_unique_values("mtm", "year"), key="mtm_year")
    
    filters = {}
    if mtm_filter_prod:
        filters['prod'] = mtm_filter_prod
    if mtm_filter_year:
        filters['year'] = int(mtm_filter_year)
    
    mtm_data = get_mtm(filters)
    if mtm_data:
        st.dataframe(pd.DataFrame(mtm_data))
    else:
        st.info("No MTM records found")

# Position Summary Page
elif page == "Position Summary":
    st.header("Position Summary")
    
    summary = get_position_summary()
    if summary:
        df = pd.DataFrame(summary)
        st.dataframe(df)
        
        # Display charts
        col1, col2 = st.columns(2)
        with col1:
            if not df.empty:
                st.bar_chart(df.set_index('prod')['total_ton'])
        with col2:
            if not df.empty:
                st.bar_chart(df.set_index('prod')['total_notion'])
    else:
        st.info("No position data available")

# PNL Summary Page
elif page == "PNL Summary":
    st.header("PNL Summary")
    
    pnl_summary = get_pnl_summary()
    if pnl_summary:
        df = pd.DataFrame(pnl_summary)
        st.dataframe(df)
        
        # Display PNL chart
        if not df.empty:
            st.bar_chart(df.set_index('prod')['total_pnl'])
    else:
        st.info("No PNL data available")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Trading Management System v2.0")
