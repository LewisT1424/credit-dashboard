import streamlit as st
import polars as pl
from utils import search_borrowers, get_borrower_detail
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Borrower Search", layout="wide")

st.title("Borrower Search & Drill-Down")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# Get unique borrower names
all_borrowers = sorted(df['borrower'].unique().to_list())

# Search interface with selectbox
st.subheader("Search by Borrower")
selected_borrower = st.selectbox(
    "Select or search for a borrower",
    options=[""] + all_borrowers,
    index=0,
    key="borrower_select_search",
    help="Start typing to search, or scroll to select"
)

# Perform search
if selected_borrower:
    results = df.filter(pl.col('borrower') == selected_borrower)
    
    if len(results) == 0:
        st.info("No borrowers found matching your search.")
    else:
        st.subheader(f"Search Results ({len(results)} loans)")
        
        # Display search results table
        results_display = results.select([
            'loan_id',
            'borrower',
            'amount',
            'rate',
            'credit_rating',
            'status',
            'sector'
        ]).with_columns([
            (pl.col('amount') / 1e6).alias('Amount (M)')
        ]).drop(['amount'])
        
        st.dataframe(results_display, width=1200, height=400)
        
        # Borrower drill-down
        st.subheader("Borrower Drill-Down")
        
        unique_borrowers = results.select('borrower').unique()['borrower'].to_list()
        selected_borrower = st.selectbox(
            "Select a borrower to view details",
            unique_borrowers,
            key="borrower_select"
        )
        
        if selected_borrower:
            detail = get_borrower_detail(df, selected_borrower)
            
            if detail:
                # Display borrower metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Exposure",
                        f"£{detail['total_exposure']/1e6:.2f}M",
                        delta=f"{detail['pct_of_portfolio']:.2f}% of portfolio"
                    )
                
                with col2:
                    st.metric(
                        "Number of Loans",
                        detail['num_loans']
                    )
                
                with col3:
                    st.metric(
                        "Weighted Avg Rate",
                        f"{detail['avg_rate']:.2f}%"
                    )
                
                with col4:
                    num_healthy = len(detail['loans'].filter(pl.col('status') == 'Performing'))
                    health_pct = (num_healthy / detail['num_loans']) * 100
                    st.metric(
                        "Performing Loans",
                        f"{num_healthy}/{detail['num_loans']}",
                        delta=f"{health_pct:.1f}%"
                    )
                
                # Display detailed loan list
                st.subheader(f"All Loans for {selected_borrower}")
                
                loans_display = detail['loans'].select([
                    'loan_id',
                    'amount',
                    'rate',
                    'credit_rating',
                    'status',
                    'sector',
                    'maturity_date'
                ]).with_columns([
                    (pl.col('amount') / 1e6).alias('Amount (M)')
                ]).drop(['amount']).sort('credit_rating')
                
                st.dataframe(loans_display, width=1200, height=500)
                
                # Risk indicators
                st.subheader("Risk Indicators")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    non_performing = len(detail['loans'].filter(pl.col('status') != 'Performing'))
                    if non_performing > 0:
                        st.warning(f"Non-Performing: {non_performing} loans")
                    else:
                        st.success("All loans performing")
                
                with col2:
                    high_risk = len(detail['loans'].filter(pl.col('credit_rating').is_in(['D', 'C', 'B'])))
                    if high_risk > 0:
                        st.warning(f"High Risk Rating: {high_risk} loans")
                    else:
                        st.success("Low risk profile")
                
                with col3:
                    speculative = len(detail['loans'].filter(pl.col('credit_rating').is_in(['BB', 'B', 'CCC'])))
                    if speculative > 0:
                        st.info(f"Speculative Grade: {speculative} loans")
                    else:
                        st.success("Investment grade")
else:
    st.info("Enter a borrower name or loan ID and click Search to get started.")
