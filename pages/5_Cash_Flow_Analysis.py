import streamlit as st
import polars as pl
from utils import calculate_cash_flow_projection
import plotly.graph_objects as go
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Cash Flow Analysis", layout="wide")

st.title("Cash Flow Projections")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# Projection parameters
col1, col2, col3 = st.columns(3)

with col1:
    months = st.slider(
        "Projection period (months)",
        min_value=6,
        max_value=60,
        value=24,
        step=6,
        key="cf_months"
    )

with col2:
    st.info(f"Projecting cash flows for {months} months")

# Calculate cash flows
cf_data = calculate_cash_flow_projection(df, months=months)

if cf_data is None:
    st.error("Unable to calculate cash flow projections. Please ensure maturity dates are present.")
    st.stop()

st.subheader("Monthly Cash Flow Projections")

# Display summary metrics
col1, col2, col3, col4 = st.columns(4)

total_interest = cf_data['interest_cf'].sum()
total_principal = cf_data['principal_cf'].sum()
total_cf = cf_data['total_cf'].sum()

with col1:
    st.metric(
        "Total Interest (24m)",
        f"£{total_interest:.2f}M"
    )

with col2:
    st.metric(
        "Total Principal (24m)",
        f"£{total_principal:.2f}M"
    )

with col3:
    st.metric(
        "Total Cash Flow",
        f"£{total_cf:.2f}M"
    )

with col4:
    avg_monthly = total_cf / months
    st.metric(
        "Avg Monthly CF",
        f"£{avg_monthly:.2f}M"
    )

# Create stacked area chart
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=cf_data['month'],
    y=cf_data['interest_cf'],
    name='Interest Income',
    mode='lines',
    line=dict(width=0.5, color='rgb(84, 153, 255)'),
    fillcolor='rgba(84, 153, 255, 0.5)',
    stackgroup='one'
))

fig.add_trace(go.Scatter(
    x=cf_data['month'],
    y=cf_data['principal_cf'],
    name='Principal Repayment',
    mode='lines',
    line=dict(width=0.5, color='rgb(50, 200, 50)'),
    fillcolor='rgba(50, 200, 50, 0.5)',
    stackgroup='one'
))

fig.update_layout(
    title=f"Portfolio Cash Flows - {months} Month Projection",
    xaxis_title="Month",
    yaxis_title="Cash Flow (£M)",
    hovermode='x unified',
    height=500,
    template='plotly_white'
)

st.plotly_chart(fig, width=1200)

# Detailed cash flow table
st.subheader("Detailed Projections")

cf_display = cf_data.select([
    'month',
    'date',
    'interest_cf',
    'principal_cf',
    'total_cf'
]).with_columns([
    pl.col('date').cast(pl.Utf8).alias('Date'),
    (pl.col('interest_cf')).alias('Interest (£M)'),
    (pl.col('principal_cf')).alias('Principal (£M)'),
    (pl.col('total_cf')).alias('Total (£M)')
]).drop(['date', 'interest_cf', 'principal_cf', 'total_cf']).rename({
    'month': 'Month'
})

# Format for display
st.dataframe(
    cf_display.with_columns([
        pl.col('Interest (£M)').round(3),
        pl.col('Principal (£M)').round(3),
        pl.col('Total (£M)').round(3)
    ]),
    width=1200,
    height=400
)

# Liquidity analysis
st.subheader("Liquidity Analysis")

# Calculate cumulative and identify cash flow gaps
cf_analysis = cf_data.with_columns([
    pl.col('total_cf').cum_sum().alias('cumulative_cf')
])

# Find month where cash flow becomes negative or positive
positive_months = cf_analysis.filter(pl.col('total_cf') > 0)
if len(positive_months) > 0:
    first_positive = positive_months.select('month')[0, 0]
    st.success(f"Positive cash flow starts in Month {first_positive}")
else:
    st.warning("Portfolio may not generate positive cash flows in projection period")

# Cumulative cash flow chart
fig_cum = go.Figure()

fig_cum.add_trace(go.Scatter(
    x=cf_analysis['month'],
    y=cf_analysis['cumulative_cf'],
    mode='lines+markers',
    name='Cumulative Cash Flow',
    line=dict(color='rgb(31, 119, 180)', width=3),
    fill='tozeroy'
))

fig_cum.update_layout(
    title="Cumulative Cash Flow",
    xaxis_title="Month",
    yaxis_title="Cumulative CF (£M)",
    hovermode='x',
    height=400,
    template='plotly_white'
)

st.plotly_chart(fig_cum, width=1200)

# Key insights
st.subheader("Key Insights")

col1, col2 = st.columns(2)

with col1:
    peak_month = cf_data.with_row_index().filter(
        pl.col('total_cf') == pl.col('total_cf').max()
    )['month'][0]
    peak_cf = cf_data['total_cf'].max()
    st.info(f"Peak monthly cash flow: £{peak_cf:.2f}M in Month {peak_month}")

with col2:
    avg_monthly = cf_data['total_cf'].mean()
    st.info(f"Average monthly cash flow: £{avg_monthly:.2f}M")
