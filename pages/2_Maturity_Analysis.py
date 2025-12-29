import streamlit as st
import polars as pl
import plotly.graph_objects as go
import logging
from utils import calculate_maturity_analysis, apply_filters

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Maturity Analysis",
    layout="wide"
)

st.title("Maturity Profile Analysis")
st.markdown("### Loan Maturity Timeline & Refinancing Risk")

if 'portfolio_data' not in st.session_state or st.session_state.portfolio_data is None:
    st.warning("Please load data on the Home page first.")
    st.stop()

df = st.session_state.portfolio_data

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
    key="mat_sector"
)
rating_filter = st.sidebar.multiselect(
    "Credit Rating", 
    ratings, 
    default=st.session_state.rating_filter,
    key="mat_rating"
)
status_filter = st.sidebar.multiselect(
    "Status", 
    statuses, 
    default=st.session_state.status_filter,
    key="mat_status"
)

min_loan = df['amount'].min() / 1e6
max_loan = df['amount'].max() / 1e6
loan_size_range = st.sidebar.slider(
    "Loan Size Range (£M)",
    float(min_loan),
    float(max_loan),
    st.session_state.loan_size_range,
    key="mat_size"
)

# Update session state
st.session_state.sector_filter = sector_filter
st.session_state.rating_filter = rating_filter
st.session_state.status_filter = status_filter
st.session_state.loan_size_range = loan_size_range

# Apply filters
filtered_df = apply_filters(df, sector_filter, rating_filter, status_filter, loan_size_range)

st.info(f"Analyzing {len(filtered_df)} of {len(df)} loans")

maturity_data = calculate_maturity_analysis(filtered_df)

if maturity_data:
    # Maturity metrics in columns
    mat_col1, mat_col2, mat_col3, mat_col4 = st.columns(4)
    
    with mat_col1:
        st.metric(
            "Weighted Avg Maturity",
            f"{maturity_data['wam_years']:.2f} years"
        )
    
    with mat_col2:
        upcoming_6m_pct = (maturity_data['upcoming_6m_amount'] / filtered_df['amount'].sum()) * 100
        st.metric(
            "Maturing in 6 Months",
            f"£{maturity_data['upcoming_6m_amount']/1e6:.1f}M",
            delta=f"{upcoming_6m_pct:.1f}% of portfolio"
        )
    
    with mat_col3:
        upcoming_12m_pct = (maturity_data['upcoming_12m_amount'] / filtered_df['amount'].sum()) * 100
        st.metric(
            "Maturing in 12 Months",
            f"£{maturity_data['upcoming_12m_amount']/1e6:.1f}M",
            delta=f"{upcoming_12m_pct:.1f}% of portfolio"
        )
    
    with mat_col4:
        refinancing_risk = "High Risk" if upcoming_6m_pct > 30 else "Medium Risk" if upcoming_6m_pct > 15 else "Low Risk"
        st.metric(
            "Refinancing Risk",
            refinancing_risk,
            delta=f"{len(maturity_data['upcoming_6m'])} loans"
        )
    
    st.divider()
    
    # Maturity profile chart and upcoming maturities
    mat_chart_col1, mat_chart_col2 = st.columns([3, 2])
    
    with mat_chart_col1:
        st.markdown("**Maturity Profile by Quarter**")
        try:
            fig_maturity = go.Figure(data=[
                go.Bar(
                    x=maturity_data['maturity_profile']['period'],
                    y=maturity_data['maturity_profile']['amount_mm'],
                    text=maturity_data['maturity_profile']['amount_mm'].round(1),
                    texttemplate='£%{text}M',
                    textposition='outside',
                    marker_color='steelblue',
                    hovertemplate='<b>%{x}</b><br>Amount: £%{y:.1f}M<br>Count: %{customdata[0]}<extra></extra>',
                    customdata=maturity_data['maturity_profile'].select(['count']).to_numpy()
                )
            ])
            fig_maturity.update_layout(
                xaxis_title="Maturity Period",
                yaxis_title="Amount (£M)",
                showlegend=False,
                height=500
            )
            st.plotly_chart(fig_maturity, width="stretch")
        except Exception as e:
            logger.error(f"Error creating maturity chart: {str(e)}")
            st.error("Could not generate maturity profile chart")
    
    with mat_chart_col2:
        st.markdown("**Upcoming Maturities (Next 6 Months)**")
        if len(maturity_data['upcoming_6m']) > 0:
            upcoming_display = maturity_data['upcoming_6m'].with_columns([
                (pl.col('amount') / 1e6).round(2).alias('amount_mm')
            ]).select([
                pl.col('loan_id').alias('Loan ID'),
                pl.col('borrower').alias('Borrower'),
                pl.col('amount_mm').alias('Amount (£M)'),
                pl.col('maturity_parsed').alias('Maturity'),
                pl.col('credit_rating').alias('Rating')
            ])
            st.dataframe(upcoming_display, width="stretch", hide_index=True, height=468)
        else:
            st.info("No loans maturing in the next 6 months")
    
    st.divider()
    
    # Upcoming maturities in 12 months table
    st.subheader("All Upcoming Maturities (Next 12 Months)")
    if len(maturity_data['upcoming_12m']) > 0:
        upcoming_12m_display = maturity_data['upcoming_12m'].with_columns([
            (pl.col('amount') / 1e6).round(2).alias('amount_mm')
        ]).select([
            pl.col('loan_id').alias('Loan ID'),
            pl.col('borrower').alias('Borrower'),
            pl.col('amount_mm').alias('Amount (£M)'),
            pl.col('rate').alias('Rate (%)'),
            pl.col('sector').alias('Sector'),
            pl.col('maturity_parsed').alias('Maturity'),
            pl.col('credit_rating').alias('Rating')
        ])
        st.dataframe(upcoming_12m_display, width="stretch", hide_index=True)
    else:
        st.info("No loans maturing in the next 12 months")
else:
    st.error("Maturity analysis requires valid maturity_date field in the dataset")
