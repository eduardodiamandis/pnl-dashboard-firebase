import streamlit as st
import pandas as pd
from datetime import datetime
from data_firebase import (
    add_trade, add_mtm, add_pos, get_trades, get_mtm, get_positions,
    update_trade, delete_trade, get_position_summary, get_pnl_summary,
    get_unique_values, get_mtm_by_trade
)

# Page configuration
st.set_page_config(page_title="Trading Management System", layout="wide")

# Title
st.title("Trading Management System")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Select Page",
    ["Add Trade", "View Trades", "Add MTM", "View MTM", "Position Summary", "PNL Summary"]
)

# Predefined options for dropdowns
PRODUCT_OPTIONS = ["Crude Oil", "Natural Gas", "Gasoline", "Diesel", "Jet Fuel", "Brent", "WTI"]
CATEGORY_OPTIONS = ["Physical", "Future", "Option", "Swap", "Forward"]
SHIP_OPTIONS = ["VLCC", "Suezmax", "Aframax", "Panamax", "Handysize"]
OPERATION_OPTIONS = ["Buy", "Sell", "Hedge", "Arbitrage"]

# Add Trade Page
if page == "Add Trade":
    st.header("Add New Trade")
    
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            prod = st.selectbox("Product*", options=PRODUCT_OPTIONS, 
                               help="Select the traded product")
            cat = st.selectbox("Category*", options=CATEGORY_OPTIONS,
                              help="Select the trade category")
            ship = st.selectbox("Vessel Type", options=SHIP_OPTIONS,
                               help="Select the vessel type for physical trades")
            year = st.number_input("Year*", min_value=2000, max_value=2100, 
                                  value=datetime.now().year,
                                  help="Trade execution year")
        
        with col2:
            op = st.selectbox("Operation Type", options=OPERATION_OPTIONS,
                             help="Type of trading operation")
            ton = st.number_input("Tonage*", min_value=0.1, format="%.2f",
                                help="Quantity in metric tons")
            lvl = st.number_input("Price Level", min_value=0.0, format="%.2f",
                                 help="Price level or strike price")
            notion = st.number_input("Notional Value*", min_value=0.1, format="%.2f",
                                   help="Total notional value in USD")
        
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            if not prod or not cat:
                st.error("Please fill all required fields (marked with *)")
            else:
                trade_id = add_trade(prod, cat, ship, year, op, ton, lvl, notion)
                if trade_id:
                    st.success(f"Trade added successfully! Trade ID: {trade_id}")

# View Trades Page
elif page == "View Trades":
    st.header("Trade Portfolio")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_prod = st.selectbox("Filter by Product", [""] + PRODUCT_OPTIONS,
                                  help="Filter trades by product type")
    with col2:
        filter_year = st.selectbox("Filter by Year", [""] + get_unique_values("trades", "year"),
                                  help="Filter trades by execution year")
    with col3:
        filter_cat = st.selectbox("Filter by Category", [""] + CATEGORY_OPTIONS,
                                 help="Filter trades by category")
    with col4:
        filter_status = st.selectbox("Filter by Status", ["", "active", "inactive"],
                                    help="Show active or inactive trades")
    
    # Apply filters
    filters = {}
    if filter_prod:
        filters['prod'] = filter_prod
    if filter_year:
        filters['year'] = int(filter_year)
    if filter_cat:
        filters['cat'] = filter_cat
    if filter_status:
        filters['status'] = filter_status
    
    # Get and display trades
    trades = get_trades(filters)
    if trades:
        # Create a clean dataframe for display
        display_data = []
        for trade in trades:
            display_data.append({
                'Trade ID': trade['id'],
                'Product': trade['prod'],
                'Category': trade['cat'],
                'Vessel': trade['ship'],
                'Year': trade['year'],
                'Operation': trade['op'],
                'Tonage': f"{trade['ton']:,.2f}",
                'Price Level': f"{trade['lvl']:,.2f}",
                'Notional': f"${trade['notion']:,.2f}",
                'Status': trade.get('status', 'active'),
                'Date': trade['date']
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Trade actions section
        st.subheader("Trade Management")
        selected_trade = st.selectbox("Select trade for actions", 
                                     [f"{t['id']} - {t['prod']} ({t['year']})" for t in trades],
                                     help="Select a trade to view details or perform actions")
        
        if selected_trade:
            trade_id = selected_trade.split(" - ")[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("View MTM History", help="View all MTM records for this trade"):
                    mtm_data = get_mtm_by_trade(trade_id)
                    if mtm_data:
                        mtm_df = pd.DataFrame(mtm_data)
                        st.dataframe(mtm_df[['date', 'mtm', 'pnl']])
                    else:
                        st.info("No MTM records found for this trade")
            
            with col2:
                if st.button("Deactivate Trade", help="Soft delete - marks trade as inactive"):
                    if delete_trade(trade_id):
                        st.rerun()
            
            with col3:
                if st.button("Refresh Data", help="Reload current view"):
                    st.rerun()
                    
    else:
        st.info("No trades found with the selected filters")

# Add MTM Page
elif page == "Add MTM":
    st.header("Mark-to-Market Valuation")
    
    # Get active trades for selection
    trades = get_trades({"status": "active"})
    if trades:
        trade_options = {f"{t['id']} - {t['prod']} ({t['year']})": t['id'] for t in trades}
        
        with st.form("mtm_form"):
            selected_trade = st.selectbox("Select Trade*", list(trade_options.keys()),
                                         help="Select the trade to update MTM valuation")
            col1, col2 = st.columns(2)
            with col1:
                mtm_value = st.number_input("MTM Value*", format="%.2f",
                                          help="Current mark-to-market value")
            with col2:
                pnl_value = st.number_input("PNL Value*", format="%.2f",
                                          help="Profit and Loss since last valuation")
            
            submitted = st.form_submit_button("Add MTM Valuation")
            if submitted:
                trade_id = trade_options[selected_trade]
                if add_mtm(trade_id, mtm_value, pnl_value):
                    st.success("MTM valuation recorded successfully")
    else:
        st.info("No active trades found. Please add trades before recording MTM valuations.")

# View MTM Page
elif page == "View MTM":
    st.header("MTM Valuation History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        mtm_filter_prod = st.selectbox("Filter by Product", [""] + PRODUCT_OPTIONS, key="mtm_prod")
    with col2:
        mtm_filter_year = st.selectbox("Filter by Year", [""] + get_unique_values("mtm", "year"), key="mtm_year")
    with col3:
        date_range = st.date_input("Date Range", [], key="mtm_date")
    
    filters = {}
    if mtm_filter_prod:
        filters['prod'] = mtm_filter_prod
    if mtm_filter_year:
        filters['year'] = int(mtm_filter_year)
    
    mtm_data = get_mtm(filters)
    if mtm_data:
        # Format MTM data for display
        display_mtm = []
        for mtm in mtm_data:
            display_mtm.append({
                'Trade ID': mtm['trade_id'],
                'Product': mtm['prod'],
                'Year': mtm['year'],
                'MTM Value': f"${mtm['mtm']:,.2f}",
                'PNL': f"${mtm['pnl']:,.2f}",
                'Valuation Date': mtm['date']
            })
        
        mtm_df = pd.DataFrame(display_mtm)
        st.dataframe(mtm_df, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        total_mtm = sum(mtm['mtm'] for mtm in mtm_data)
        total_pnl = sum(mtm['pnl'] for mtm in mtm_data)
        
        with col1:
            st.metric("Total MTM Value", f"${total_mtm:,.2f}")
        with col2:
            st.metric("Total PNL", f"${total_pnl:,.2f}")
        with col3:
            st.metric("Total Valuations", len(mtm_data))
            
    else:
        st.info("No MTM records found with the selected filters")

# Position Summary Page
elif page == "Position Summary":
    st.header("Position Summary")
    
    summary = get_position_summary()
    if summary:
        # Format summary data
        display_summary = []
        for item in summary:
            display_summary.append({
                'Product': item['prod'],
                'Year': item['year'],
                'Total Tonage': f"{item['total_ton']:,.2f}",
                'Total Notional': f"${item['total_notion']:,.2f}",
                'Trade Count': item['trades_count']
            })
        
        df = pd.DataFrame(display_summary)
        st.dataframe(df, use_container_width=True)
        
        # Display charts
        st.subheader("Position Visualization")
        col1, col2 = st.columns(2)
        
        with col1:
            if not df.empty:
                chart_data = pd.DataFrame(summary)
                chart_data['Total Tonage Num'] = [item['total_ton'] for item in summary]
                st.bar_chart(chart_data.set_index('prod')['Total Tonage Num'])
        
        with col2:
            if not df.empty:
                chart_data['Total Notional Num'] = [item['total_notion'] for item in summary]
                st.bar_chart(chart_data.set_index('prod')['Total Notional Num'])
                
    else:
        st.info("No position data available. Add trades to see position summaries.")

# PNL Summary Page
elif page == "PNL Summary":
    st.header("Profit & Loss Summary")
    
    pnl_summary = get_pnl_summary()
    if pnl_summary:
        # Format PNL data
        display_pnl = []
        for item in pnl_summary:
            display_pnl.append({
                'Product': item['prod'],
                'Year': item['year'],
                'Total MTM': f"${item['total_mtm']:,.2f}",
                'Total PNL': f"${item['total_pnl']:,.2f}",
                'Valuation Count': item['records_count']
            })
        
        df = pd.DataFrame(display_pnl)
        st.dataframe(df, use_container_width=True)
        
        # PNL metrics
        total_portfolio_pnl = sum(item['total_pnl'] for item in pnl_summary)
        total_portfolio_mtm = sum(item['total_mtm'] for item in pnl_summary)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Portfolio Total PNL", f"${total_portfolio_pnl:,.2f}")
        with col2:
            st.metric("Portfolio Total MTM", f"${total_portfolio_mtm:,.2f}")
        
        # PNL chart
        st.subheader("PNL Distribution")
        if not df.empty:
            chart_data = pd.DataFrame(pnl_summary)
            chart_data['Total PNL Num'] = [item['total_pnl'] for item in pnl_summary]
            st.bar_chart(chart_data.set_index('prod')['Total PNL Num'])
            
    else:
        st.info("No PNL data available. Add MTM valuations to see PNL summaries.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Trading Management System v2.0")
