import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Default Probability Model", layout="wide")

st.title("Default Probability Model")
st.markdown("### Credit Risk & Expected Loss Analysis")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# Load default rates lookup table
try:
    default_rates = pl.read_csv('data/default_rates.csv')
except Exception as e:
    st.error(f"Error loading default rates: {str(e)}")
    st.stop()

# ====================PORTFOLIO-LEVEL PD ====================

st.subheader("Portfolio Probability of Default (PD)")

# Join portfolio with default rates
portfolio_pd = df.join(default_rates, on='credit_rating', how='left')

# Calculate weighted PD
total_exposure = portfolio_pd.select(pl.col('amount').sum()).item()
weighted_pd = portfolio_pd.select(
    (pl.col('amount') * pl.col('default_probability')).sum() / total_exposure
).item()

# Calculate expected loss
expected_loss = portfolio_pd.select(
    (pl.col('amount') * pl.col('default_probability') * (1 - pl.col('recovery_rate'))).sum()
).item()

# Risk-weighted exposure
risk_weighted_exposure = portfolio_pd.select(
    (pl.col('amount') * pl.col('risk_weight')).sum()
).item()

# Display key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Portfolio PD",
        f"{weighted_pd*100:.3f}%",
        help="Weighted average probability of default"
    )

with col2:
    st.metric(
        "Expected Loss",
        f"£{expected_loss/1e6:.2f}M",
        delta=f"{(expected_loss/total_exposure)*100:.2f}% of portfolio",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "Risk-Weighted Assets",
        f"£{risk_weighted_exposure/1e6:.1f}M",
        help="Total exposure adjusted for credit risk"
    )

with col4:
    avg_recovery = portfolio_pd.select(
        pl.col('recovery_rate').mean()
    ).item()
    st.metric(
        "Avg Recovery Rate",
        f"{avg_recovery*100:.1f}%",
        help="Expected recovery in case of default"
    )

# ==================== PD BY RATING ====================

st.subheader("Default Probability by Credit Rating")

col1, col2 = st.columns([3, 2])

with col1:
    # Group by rating
    rating_pd = portfolio_pd.group_by('credit_rating').agg([
        pl.col('loan_id').count().alias('count'),
        pl.col('amount').sum().alias('exposure'),
        pl.col('default_probability').mean().alias('avg_pd'),
        (pl.col('amount') * pl.col('default_probability') * (1 - pl.col('recovery_rate'))).sum().alias('expected_loss')
    ]).sort('avg_pd', descending=True)
    
    # Create stacked bar chart
    fig_rating = go.Figure()
    
    fig_rating.add_trace(go.Bar(
        name='Exposure',
        x=rating_pd['credit_rating'].to_list(),
        y=rating_pd['exposure'].to_list(),
        marker_color='lightblue',
        yaxis='y'
    ))
    
    fig_rating.add_trace(go.Scatter(
        name='Default Probability',
        x=rating_pd['credit_rating'].to_list(),
        y=[p*100 for p in rating_pd['avg_pd'].to_list()],
        marker_color='red',
        mode='lines+markers',
        yaxis='y2'
    ))
    
    fig_rating.update_layout(
        title='Exposure vs Default Probability by Rating',
        xaxis_title='Credit Rating',
        yaxis_title='Exposure (£)',
        yaxis2=dict(
            title='Default Probability (%)',
            overlaying='y',
            side='right'
        ),
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_rating, width=900)

with col2:
    st.write("**Rating Statistics**")
    
    # Display table
    rating_summary = rating_pd.select([
        'credit_rating',
        'count',
        pl.col('avg_pd').map_elements(lambda x: f"{x*100:.3f}%", return_dtype=pl.Utf8).alias('PD'),
        pl.col('expected_loss').map_elements(lambda x: f"£{x/1e6:.2f}M", return_dtype=pl.Utf8).alias('Exp Loss')
    ])
    
    st.dataframe(
        rating_summary.to_pandas(),
        hide_index=True,
        use_container_width=True,
        height=350
    )

# ==================== EXPECTED LOSS DISTRIBUTION ====================

st.subheader("Expected Loss Distribution")

col1, col2 = st.columns(2)

with col1:
    # Top 10 riskiest loans
    risky_loans = portfolio_pd.with_columns([
        (pl.col('amount') * pl.col('default_probability') * (1 - pl.col('recovery_rate'))).alias('loan_expected_loss')
    ]).sort('loan_expected_loss', descending=True).head(10)
    
    fig_risky = px.bar(
        risky_loans.to_dicts(),
        x='loan_id',
        y='loan_expected_loss',
        color='credit_rating',
        title='Top 10 Loans by Expected Loss',
        labels={'loan_expected_loss': 'Expected Loss (£)', 'loan_id': 'Loan ID'},
        color_discrete_sequence=px.colors.sequential.Reds_r
    )
    fig_risky.update_layout(height=400)
    st.plotly_chart(fig_risky, width=600)

with col2:
    # Expected loss by sector
    sector_el = portfolio_pd.group_by('sector').agg([
        pl.col('amount').sum().alias('exposure'),
        (pl.col('amount') * pl.col('default_probability') * (1 - pl.col('recovery_rate'))).sum().alias('expected_loss')
    ]).with_columns([
        (pl.col('expected_loss') / pl.col('exposure') * 100).alias('loss_rate')
    ]).sort('expected_loss', descending=True).head(10)
    
    fig_sector = px.bar(
        sector_el.to_dicts(),
        x='sector',
        y='expected_loss',
        title='Expected Loss by Sector',
        labels={'expected_loss': 'Expected Loss (£)', 'sector': 'Sector'},
        color='loss_rate',
        color_continuous_scale='OrRd'
    )
    fig_sector.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_sector, width=600)

# ==================== RISK CONCENTRATION ====================

st.subheader("Risk Concentration Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    # High risk loans (PD > 5%)
    high_risk = len(portfolio_pd.filter(pl.col('default_probability') > 0.05))
    high_risk_exposure = portfolio_pd.filter(
        pl.col('default_probability') > 0.05
    ).select(pl.col('amount').sum()).item()
    
    st.metric(
        "High Risk Loans (PD > 5%)",
        high_risk,
        delta=f"£{high_risk_exposure/1e6:.1f}M exposure",
        delta_color="inverse"
    )

with col2:
    # Investment grade
    inv_grade = len(portfolio_pd.filter(
        pl.col('credit_rating').is_in(['A', 'A-', 'BBB+', 'BBB', 'BBB-'])
    ))
    inv_grade_exp = portfolio_pd.filter(
        pl.col('credit_rating').is_in(['A', 'A-', 'BBB+', 'BBB', 'BBB-'])
    ).select(pl.col('amount').sum()).item()
    
    st.metric(
        "Investment Grade",
        inv_grade,
        delta=f"{(inv_grade_exp/total_exposure)*100:.1f}% of portfolio"
    )

with col3:
    # Speculative grade
    spec_grade = len(portfolio_pd.filter(
        pl.col('credit_rating').is_in(['BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC'])
    ))
    spec_grade_exp = portfolio_pd.filter(
        pl.col('credit_rating').is_in(['BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC'])
    ).select(pl.col('amount').sum()).item()
    
    st.metric(
        "Speculative Grade",
        spec_grade,
        delta=f"{(spec_grade_exp/total_exposure)*100:.1f}% of portfolio",
        delta_color="inverse"
    )

# ==================== DETAILED LOAN ANALYSIS ====================

st.subheader("Loan-Level Risk Analysis")

# Add filters
col1, col2, col3 = st.columns(3)

with col1:
    rating_filter = st.multiselect(
        "Filter by Rating",
        options=sorted(df['credit_rating'].unique().to_list()),
        default=None
    )

with col2:
    sector_filter = st.multiselect(
        "Filter by Sector",
        options=sorted(df['sector'].unique().to_list()),
        default=None
    )

with col3:
    min_pd = st.slider(
        "Minimum PD (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.1
    )

# Apply filters
filtered_portfolio = portfolio_pd

if rating_filter:
    filtered_portfolio = filtered_portfolio.filter(
        pl.col('credit_rating').is_in(rating_filter)
    )

if sector_filter:
    filtered_portfolio = filtered_portfolio.filter(
        pl.col('sector').is_in(sector_filter)
    )

if min_pd is not None and min_pd > 0:
    filtered_portfolio = filtered_portfolio.filter(
        pl.col('default_probability') >= (min_pd / 100)
    )

# Calculate loan-level metrics
loan_analysis = filtered_portfolio.with_columns([
    (pl.col('amount') * pl.col('default_probability')).alias('expected_default_loss'),
    (pl.col('amount') * pl.col('default_probability') * (1 - pl.col('recovery_rate'))).alias('net_expected_loss'),
    (pl.col('default_probability') * 100).alias('pd_pct')
]).select([
    'loan_id',
    'borrower',
    'amount',
    'credit_rating',
    'sector',
    'pd_pct',
    pl.col('recovery_rate').map_elements(lambda x: f"{x*100:.0f}%", return_dtype=pl.Utf8).alias('recovery'),
    'expected_default_loss',
    'net_expected_loss'
]).sort('net_expected_loss', descending=True)

st.write(f"**Showing {len(loan_analysis)} loans**")

if len(loan_analysis) > 0:
    # Format for display
    display_df = loan_analysis.to_pandas()
    display_df['amount'] = display_df['amount'].apply(lambda x: f"£{x/1e6:.2f}M")
    display_df['pd_pct'] = display_df['pd_pct'].apply(lambda x: f"{x:.3f}%")
    display_df['expected_default_loss'] = display_df['expected_default_loss'].apply(lambda x: f"£{x/1e6:.3f}M")
    display_df['net_expected_loss'] = display_df['net_expected_loss'].apply(lambda x: f"£{x/1e6:.3f}M")

    display_df.columns = ['Loan ID', 'Borrower', 'Amount', 'Rating', 'Sector', 'PD', 'Recovery', 'Gross Loss', 'Net Loss']

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=400
    )
else:
    st.info("No loans match the selected filters")

# ==================== DOWNLOAD ====================

st.subheader("Export Analysis")

col1, col2 = st.columns(2)

with col1:
    # Export full analysis
    if len(loan_analysis) > 0:
        csv_data = loan_analysis.write_csv()
        st.download_button(
            label="📥 Download Risk Analysis (CSV)",
            data=csv_data,
            file_name=f"risk_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to export")

with col2:
    # Summary stats
    if len(filtered_portfolio) > 0:
        total_exposure = filtered_portfolio.select(pl.col('amount').sum()).item()
        avg_pd = filtered_portfolio.select(pl.col('default_probability').mean()).item()
        total_el = filtered_portfolio.select((pl.col('amount') * pl.col('default_probability') * (1 - pl.col('recovery_rate'))).sum()).item()
        
        st.write("**Portfolio Summary:**")
        st.write(f"- Total Loans: {len(filtered_portfolio)}")
        st.write(f"- Total Exposure: £{total_exposure/1e6:.1f}M")
        st.write(f"- Avg PD: {avg_pd*100:.3f}%")
        st.write(f"- Total Expected Loss: £{total_el/1e6:.2f}M")
    else:
        st.warning("⚠️ No loans match the selected filters. Adjust filters to view data.")

st.info("💡 **Note:** Default probabilities and recovery rates are based on historical data and should be reviewed regularly. Expected loss = Exposure × PD × (1 - Recovery Rate)")
