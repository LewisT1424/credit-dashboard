import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import logging
from utils import calculate_concentration_metrics, apply_filters

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Concentration Risk",
    layout="wide"
)

st.title("Concentration Risk Analysis")
st.markdown("### Single Name Exposure & Herfindahl Index")

if st.session_state.df is None:
    st.warning("Please upload portfolio data on the Home page first.")
    st.stop()

df = st.session_state.df

# Sidebar filters
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
    key="conc_sector"
)
rating_filter = st.sidebar.multiselect(
    "Credit Rating", 
    ratings, 
    default=st.session_state.rating_filter,
    key="conc_rating"
)
status_filter = st.sidebar.multiselect(
    "Status", 
    statuses, 
    default=st.session_state.status_filter,
    key="conc_status"
)

min_loan = df['amount'].min() / 1e6
max_loan = df['amount'].max() / 1e6
loan_size_range = st.sidebar.slider(
    "Loan Size Range (£M)",
    float(min_loan),
    float(max_loan),
    st.session_state.loan_size_range,
    key="conc_size"
)

# Update session state
st.session_state.sector_filter = sector_filter
st.session_state.rating_filter = rating_filter
st.session_state.status_filter = status_filter
st.session_state.loan_size_range = loan_size_range

# Apply filters
filtered_df = apply_filters(df, sector_filter, rating_filter, status_filter, loan_size_range)

st.info(f"Analyzing {len(filtered_df)} of {len(df)} loans")

concentration_data = calculate_concentration_metrics(filtered_df)

if concentration_data:
    # Concentration alerts
    if len(concentration_data['high_concentration_loans']) > 0:
        st.error(f"Alert: {len(concentration_data['high_concentration_loans'])} loan(s) exceed 10% single-name concentration limit")
    
    # Concentration metrics
    conc_col1, conc_col2, conc_col3 = st.columns(3)
    
    with conc_col1:
        top_exposure_pct = concentration_data['single_name_top10']['pct_portfolio'][0]
        st.metric(
            "Largest Single Exposure",
            f"{top_exposure_pct:.1f}%",
            delta="High Risk" if top_exposure_pct > 10 else "Acceptable"
        )
    
    with conc_col2:
        top3_exposure = concentration_data['single_name_top10']['pct_portfolio'][:3].sum()
        st.metric(
            "Top 3 Concentration",
            f"{top3_exposure:.1f}%",
            delta="High Risk" if top3_exposure > 30 else "Acceptable"
        )
    
    with conc_col3:
        st.metric(
            "Sector HHI Score",
            f"{concentration_data['hhi_score']:.0f}",
            delta=concentration_data['hhi_risk']
        )
    
    st.divider()
    
    # Concentration charts
    conc_chart_col1, conc_chart_col2 = st.columns(2)
    
    with conc_chart_col1:
        st.markdown("**Top 10 Single Name Exposures**")
        try:
            fig_single_name = go.Figure(data=[
                go.Bar(
                    x=concentration_data['single_name_top10']['borrower'],
                    y=concentration_data['single_name_top10']['pct_portfolio'],
                    text=concentration_data['single_name_top10']['pct_portfolio'].round(1),
                    texttemplate='%{text}%',
                    textposition='outside',
                    marker_color=['red' if x > 10 else 'orange' if x > 7 else 'steelblue' 
                                 for x in concentration_data['single_name_top10']['pct_portfolio']]
                )
            ])
            
            # Add 10% limit line
            fig_single_name.add_hline(
                y=10, 
                line_dash="dash", 
                line_color="red",
                annotation_text="10% Limit",
                annotation_position="right"
            )
            
            fig_single_name.update_layout(
                xaxis_title="Borrower",
                yaxis_title="% of Portfolio",
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig_single_name, width="stretch")
        except Exception as e:
            logger.error(f"Error creating single name chart: {str(e)}")
            st.error("Could not generate concentration chart")
    
    with conc_chart_col2:
        st.markdown("**Concentration by Credit Rating**")
        try:
            fig_rating_conc = px.pie(
                concentration_data['rating_concentration'],
                values='pct_portfolio',
                names='credit_rating',
                title=f"HHI: {concentration_data['hhi_score']:.0f} ({concentration_data['hhi_level']})",
                height=500
            )
            fig_rating_conc.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_rating_conc, width="stretch")
        except Exception as e:
            logger.error(f"Error creating rating concentration chart: {str(e)}")
            st.error("Could not generate rating concentration chart")
    
    st.divider()
    
    # Detailed tables
    table_col1, table_col2 = st.columns(2)
    
    with table_col1:
        st.subheader("Top 10 Exposures Detail")
        st.dataframe(
            concentration_data['single_name_top10'].with_columns([
                (pl.col('amount') / 1e6).round(2).alias('amount_mm')
            ]).select([
                pl.col('loan_id').alias('Loan ID'),
                pl.col('borrower').alias('Borrower'),
                pl.col('amount_mm').alias('Amount (£M)'),
                pl.col('pct_portfolio').round(1).alias('% Portfolio'),
                pl.col('credit_rating').alias('Rating'),
                pl.col('sector').alias('Sector'),
                pl.col('status').alias('Status')
            ]),
            width="stretch",
            hide_index=True
        )
    
    with table_col2:
        st.subheader("Rating Concentration Detail")
        st.dataframe(
            concentration_data['rating_concentration'].select([
                pl.col('credit_rating').alias('Rating'),
                pl.col('count').alias('# Loans'),
                pl.col('amount_mm').round(2).alias('Amount (£M)'),
                pl.col('pct_portfolio').round(1).alias('% Portfolio')
            ]),
            width="stretch",
            hide_index=True
        )
