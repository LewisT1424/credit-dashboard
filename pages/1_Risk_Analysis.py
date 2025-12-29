import streamlit as st
import polars as pl
import plotly.graph_objects as go
import logging
from utils import calculate_risk_metrics, apply_filters

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Risk Analysis",
    layout="wide"
)

st.title("Risk Analysis")
st.markdown("### Portfolio Status & Sector Risk Analysis")

if st.session_state.df is None:
    st.warning("Please upload portfolio data on the Home page first.")
    st.stop()

df = st.session_state.df

# Sidebar filters (reuse from session state)
st.sidebar.subheader("Filters")

sectors = sorted(df['sector'].unique().to_list())
ratings = sorted(df['credit_rating'].unique().to_list())
statuses = sorted(df['status'].unique().to_list())

# Initialize filter defaults in session state if not present
if 'sector_filter' not in st.session_state:
    st.session_state.sector_filter = sectors
if 'rating_filter' not in st.session_state:
    st.session_state.rating_filter = ratings
if 'status_filter' not in st.session_state:
    st.session_state.status_filter = statuses
if 'loan_size_range' not in st.session_state:
    min_loan = df['amount'].min() / 1e6
    max_loan = df['amount'].max() / 1e6
    st.session_state.loan_size_range = (float(min_loan), float(max_loan))

sector_filter = st.sidebar.multiselect(
    "Sector", 
    sectors, 
    default=st.session_state.sector_filter,
    key="risk_sector"
)
rating_filter = st.sidebar.multiselect(
    "Credit Rating", 
    ratings, 
    default=st.session_state.rating_filter,
    key="risk_rating"
)
status_filter = st.sidebar.multiselect(
    "Status", 
    statuses, 
    default=st.session_state.status_filter,
    key="risk_status"
)

min_loan = df['amount'].min() / 1e6
max_loan = df['amount'].max() / 1e6
loan_size_range = st.sidebar.slider(
    "Loan Size Range (£M)",
    float(min_loan),
    float(max_loan),
    st.session_state.loan_size_range,
    key="risk_size"
)

# Update session state
st.session_state.sector_filter = sector_filter
st.session_state.rating_filter = rating_filter
st.session_state.status_filter = status_filter
st.session_state.loan_size_range = loan_size_range

# Apply filters
filtered_df = apply_filters(df, sector_filter, rating_filter, status_filter, loan_size_range)

st.info(f"Analyzing {len(filtered_df)} of {len(df)} loans")

risk_metrics = calculate_risk_metrics(filtered_df)

if risk_metrics:
    risk_col1, risk_col2 = st.columns(2)
    
    with risk_col1:
        st.markdown("**Portfolio Status Breakdown**")
        
        try:
            status_data = risk_metrics['status_breakdown']
            
            fig_status = go.Figure(data=[
                go.Bar(
                    x=status_data['status'],
                    y=status_data['pct_value'],
                    text=status_data['pct_value'].round(1),
                    texttemplate='%{text}%',
                    textposition='outside',
                    marker_color=['green' if s == 'Active' else 'orange' if s == 'Watch List' else 'red' 
                                 for s in status_data['status']]
                )
            ])
            fig_status.update_layout(
                title="% of Portfolio Value by Status",
                xaxis_title="Status",
                yaxis_title="% of Portfolio",
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig_status, width="stretch")
            
            # Status table
            st.dataframe(
                status_data.select([
                    pl.col('status').alias('Status'),
                    pl.col('count').alias('# Loans'),
                    pl.col('value_mm').round(2).alias('Value (£M)'),
                    pl.col('pct_value').round(1).alias('% Value')
                ]),
                width="stretch",
                hide_index=True
            )
        except Exception as e:
            logger.error(f"Error creating status chart: {str(e)}")
            st.error("Could not generate status breakdown chart")
    
    with risk_col2:
        st.markdown("**Sector Concentration Risk**")
        
        try:
            top_sectors = risk_metrics['sector_concentration'].head(5)
            
            fig_sector_bar = go.Figure(data=[
                go.Bar(
                    x=top_sectors['sector'],
                    y=top_sectors['pct_value'],
                    text=top_sectors['pct_value'].round(1),
                    texttemplate='%{text}%',
                    textposition='outside'
                )
            ])
            fig_sector_bar.update_layout(
                title="Top 5 Sector Concentrations (% Value)",
                xaxis_title="Sector",
                yaxis_title="% of Portfolio",
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig_sector_bar, width="stretch")
            
            # Full sector table
            st.dataframe(
                risk_metrics['sector_concentration'].select([
                    pl.col('sector').alias('Sector'),
                    pl.col('count').alias('# Loans'),
                    pl.col('value_mm').round(2).alias('Value (£M)'),
                    pl.col('pct_value').round(1).alias('% Value')
                ]),
                width="stretch",
                hide_index=True
            )
        except Exception as e:
            logger.error(f"Error creating sector bar chart: {str(e)}")
            st.error("Could not generate sector concentration chart")
