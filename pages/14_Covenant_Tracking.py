import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Covenant Tracking", layout="wide")

st.title("Financial Covenant Tracking")
st.markdown("### Monitor Covenant Compliance & Breaches")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# ==================== COVENANT THRESHOLDS ====================

st.subheader("Covenant Thresholds")

# Define covenant limits
col1, col2, col3 = st.columns(3)

with col1:
    debt_eq_limit = st.number_input(
        "Debt-to-Equity Max",
        min_value=1.0,
        max_value=10.0,
        value=3.5,
        step=0.1,
        help="Maximum allowed debt-to-equity ratio"
    )

with col2:
    ic_limit = st.number_input(
        "Interest Coverage Min",
        min_value=1.0,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="Minimum required interest coverage ratio"
    )

with col3:
    leverage_limit = st.number_input(
        "Leverage Ratio Max",
        min_value=1.0,
        max_value=10.0,
        value=4.0,
        step=0.1,
        help="Maximum allowed leverage ratio"
    )

# ==================== COVENANT COMPLIANCE OVERVIEW ====================

st.subheader("Portfolio Covenant Compliance")

# Check covenant compliance
df_covenants = df.with_columns([
    (pl.col('debt_to_equity') > debt_eq_limit).alias('debt_eq_breach'),
    (pl.col('interest_coverage') < ic_limit).alias('ic_breach'),
    (pl.col('leverage_ratio') > leverage_limit).alias('leverage_breach')
]).with_columns([
    (pl.col('debt_eq_breach') | pl.col('ic_breach') | pl.col('leverage_breach')).alias('any_breach')
])

# Calculate compliance stats
total_loans = len(df_covenants)
debt_eq_breaches = len(df_covenants.filter(pl.col('debt_eq_breach')))
ic_breaches = len(df_covenants.filter(pl.col('ic_breach')))
leverage_breaches = len(df_covenants.filter(pl.col('leverage_breach')))
total_breaches = len(df_covenants.filter(pl.col('any_breach')))

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    compliant = total_loans - total_breaches
    compliance_pct = (compliant / total_loans) * 100
    st.metric(
        "Compliant Loans",
        compliant,
        delta=f"{compliance_pct:.1f}% of portfolio"
    )

with col2:
    breach_exposure = df_covenants.filter(pl.col('any_breach')).select(pl.col('amount').sum()).item()
    total_exposure = df_covenants.select(pl.col('amount').sum()).item()
    st.metric(
        "Breach Exposure",
        f"£{breach_exposure/1e6:.1f}M",
        delta=f"{(breach_exposure/total_exposure)*100:.1f}% of portfolio",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "Total Breaches",
        total_breaches,
        delta=f"{debt_eq_breaches + ic_breaches + leverage_breaches} violations",
        delta_color="inverse" if total_breaches > 0 else "normal"
    )

with col4:
    # Loans with multiple breaches
    multiple_breaches = len(df_covenants.filter(
        (pl.col('debt_eq_breach').cast(pl.Int32) + 
         pl.col('ic_breach').cast(pl.Int32) + 
         pl.col('leverage_breach').cast(pl.Int32)) > 1
    ))
    st.metric(
        "Multiple Breaches",
        multiple_breaches,
        help="Loans violating 2+ covenants"
    )

# ==================== BREACH BREAKDOWN ====================

st.subheader("Covenant Breach Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    # Create breach summary
    breach_summary = pl.DataFrame({
        'covenant': ['Debt-to-Equity', 'Interest Coverage', 'Leverage Ratio'],
        'breaches': [debt_eq_breaches, ic_breaches, leverage_breaches],
        'threshold': [f'>{debt_eq_limit}', f'<{ic_limit}', f'>{leverage_limit}']
    })
    
    fig_breach = px.bar(
        breach_summary.to_dicts(),
        x='covenant',
        y='breaches',
        text='breaches',
        title='Covenant Breaches by Type',
        labels={'breaches': 'Number of Loans', 'covenant': 'Covenant Type'},
        color='breaches',
        color_continuous_scale='Reds'
    )
    fig_breach.update_traces(textposition='outside')
    fig_breach.update_layout(height=400)
    st.plotly_chart(fig_breach, width=800)

with col2:
    st.write("**Breach Summary**")
    st.write("")
    
    for _, row in breach_summary.to_pandas().iterrows():
        st.write(f"**{row['covenant']}**")
        st.write(f"- Threshold: {row['threshold']}")
        st.write(f"- Breaches: {round(row['breaches'])}")
        st.write(f"- % of Portfolio: {round((row['breaches']/total_loans)*100, 1)}%")
        st.write("")

# ==================== COVENANT DISTRIBUTION ====================

st.subheader("Covenant Metrics Distribution")

col1, col2, col3 = st.columns(3)

with col1:
    # Debt-to-Equity histogram
    fig_de = px.histogram(
        df.to_dicts(),
        x='debt_to_equity',
        nbins=20,
        title='Debt-to-Equity Distribution',
        labels={'debt_to_equity': 'Debt-to-Equity Ratio'},
        color_discrete_sequence=['lightblue']
    )
    fig_de.add_vline(x=debt_eq_limit, line_dash="dash", line_color="red", 
                     annotation_text=f"Limit: {debt_eq_limit}")
    fig_de.update_layout(height=300)
    st.plotly_chart(fig_de, width=400)

with col2:
    # Interest Coverage histogram
    fig_ic = px.histogram(
        df.to_dicts(),
        x='interest_coverage',
        nbins=20,
        title='Interest Coverage Distribution',
        labels={'interest_coverage': 'Interest Coverage Ratio'},
        color_discrete_sequence=['lightgreen']
    )
    fig_ic.add_vline(x=ic_limit, line_dash="dash", line_color="red",
                     annotation_text=f"Min: {ic_limit}")
    fig_ic.update_layout(height=300)
    st.plotly_chart(fig_ic, width=400)

with col3:
    # Leverage histogram
    fig_lev = px.histogram(
        df.to_dicts(),
        x='leverage_ratio',
        nbins=20,
        title='Leverage Ratio Distribution',
        labels={'leverage_ratio': 'Leverage Ratio'},
        color_discrete_sequence=['lightyellow']
    )
    fig_lev.add_vline(x=leverage_limit, line_dash="dash", line_color="red",
                      annotation_text=f"Limit: {leverage_limit}")
    fig_lev.update_layout(height=300)
    st.plotly_chart(fig_lev, width=400)

# ==================== BREACH DETAILS ====================

st.subheader("Loans with Covenant Breaches")

# Filter options
col1, col2, col3 = st.columns(3)

with col1:
    breach_filter = st.selectbox(
        "Filter by Breach Type",
        options=['All Breaches', 'Debt-to-Equity', 'Interest Coverage', 'Leverage', 'Multiple Breaches', 'No Breaches']
    )

with col2:
    rating_filter = st.multiselect(
        "Filter by Rating",
        options=sorted(df['credit_rating'].unique().to_list()),
        default=None
    )

with col3:
    sector_filter = st.multiselect(
        "Filter by Sector",
        options=sorted(df['sector'].unique().to_list()),
        default=None
    )

# Apply filters
filtered_df = df_covenants

if breach_filter == 'Debt-to-Equity':
    filtered_df = filtered_df.filter(pl.col('debt_eq_breach'))
elif breach_filter == 'Interest Coverage':
    filtered_df = filtered_df.filter(pl.col('ic_breach'))
elif breach_filter == 'Leverage':
    filtered_df = filtered_df.filter(pl.col('leverage_breach'))
elif breach_filter == 'Multiple Breaches':
    filtered_df = filtered_df.filter(
        (pl.col('debt_eq_breach').cast(pl.Int32) + 
         pl.col('ic_breach').cast(pl.Int32) + 
         pl.col('leverage_breach').cast(pl.Int32)) > 1
    )
elif breach_filter == 'No Breaches':
    filtered_df = filtered_df.filter(~pl.col('any_breach'))
elif breach_filter == 'All Breaches':
    filtered_df = filtered_df.filter(pl.col('any_breach'))

if rating_filter:
    filtered_df = filtered_df.filter(pl.col('credit_rating').is_in(rating_filter))

if sector_filter:
    filtered_df = filtered_df.filter(pl.col('sector').is_in(sector_filter))

# Display breach details
if len(filtered_df) > 0:
    breach_detail = filtered_df.select([
        'loan_id',
        'borrower',
        'amount',
        'credit_rating',
        'sector',
        'debt_to_equity',
        'interest_coverage',
        'leverage_ratio',
        'debt_eq_breach',
        'ic_breach',
        'leverage_breach'
    ]).sort('amount', descending=True)
    
    st.write(f"**Showing {len(breach_detail)} loans**")
    
    # Format for display
    display_df = breach_detail.to_pandas()
    display_df['amount'] = display_df['amount'].apply(lambda x: f"£{x/1e6:.2f}M")
    display_df['debt_to_equity'] = display_df['debt_to_equity'].apply(lambda x: f"{x:.2f}")
    display_df['interest_coverage'] = display_df['interest_coverage'].apply(lambda x: f"{x:.2f}")
    display_df['leverage_ratio'] = display_df['leverage_ratio'].apply(lambda x: f"{x:.2f}")
    display_df['debt_eq_breach'] = display_df['debt_eq_breach'].apply(lambda x: '🔴' if x else '✅')
    display_df['ic_breach'] = display_df['ic_breach'].apply(lambda x: '🔴' if x else '✅')
    display_df['leverage_breach'] = display_df['leverage_breach'].apply(lambda x: '🔴' if x else '✅')
    
    display_df.columns = ['Loan ID', 'Borrower', 'Amount', 'Rating', 'Sector', 'D/E', 'IC', 'Leverage', 'D/E ✓', 'IC ✓', 'Lev ✓']
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=400
    )
else:
    st.info("No loans match the selected filters")

# ==================== SECTOR & RATING ANALYSIS ====================

st.subheader("Covenant Performance by Segment")

col1, col2 = st.columns(2)

with col1:
    # Breach rate by sector
    sector_breach = df_covenants.group_by('sector').agg([
        pl.col('loan_id').count().alias('total_loans'),
        pl.col('any_breach').sum().alias('breach_count')
    ]).with_columns([
        (pl.col('breach_count') / pl.col('total_loans') * 100).alias('breach_rate')
    ]).sort('breach_rate', descending=True)
    
    fig_sector = px.bar(
        sector_breach.to_dicts(),
        x='sector',
        y='breach_rate',
        title='Covenant Breach Rate by Sector',
        labels={'breach_rate': 'Breach Rate (%)', 'sector': 'Sector'},
        color='breach_rate',
        color_continuous_scale='Reds'
    )
    fig_sector.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_sector, width=600)

with col2:
    # Breach rate by rating
    rating_breach = df_covenants.group_by('credit_rating').agg([
        pl.col('loan_id').count().alias('total_loans'),
        pl.col('any_breach').sum().alias('breach_count')
    ]).with_columns([
        (pl.col('breach_count') / pl.col('total_loans') * 100).alias('breach_rate')
    ]).sort('credit_rating')
    
    fig_rating = px.bar(
        rating_breach.to_dicts(),
        x='credit_rating',
        y='breach_rate',
        title='Covenant Breach Rate by Credit Rating',
        labels={'breach_rate': 'Breach Rate (%)', 'credit_rating': 'Credit Rating'},
        color='breach_rate',
        color_continuous_scale='OrRd'
    )
    fig_rating.update_layout(height=400)
    st.plotly_chart(fig_rating, width=600)

# ==================== ACTION ITEMS ====================

st.subheader("Recommended Actions")

actions = []

# Critical breaches
critical = df_covenants.filter(
    (pl.col('debt_eq_breach').cast(pl.Int32) + 
     pl.col('ic_breach').cast(pl.Int32) + 
     pl.col('leverage_breach').cast(pl.Int32)) >= 2
)

if len(critical) > 0:
    critical_exp = critical.select(pl.col('amount').sum()).item()
    actions.append(("🔴 URGENT", f"{len(critical)} loans with multiple covenant breaches (£{critical_exp/1e6:.1f}M) - immediate review required"))

# High leverage
high_leverage = df_covenants.filter(pl.col('leverage_ratio') > leverage_limit * 1.2)
if len(high_leverage) > 0:
    actions.append(("🟠 PRIORITY", f"{len(high_leverage)} loans exceed leverage limit by >20% - restructuring discussions recommended"))

# Low interest coverage
low_ic = df_covenants.filter(pl.col('interest_coverage') < ic_limit * 0.8)
if len(low_ic) > 0:
    actions.append(("🟠 PRIORITY", f"{len(low_ic)} loans with critically low interest coverage - cashflow monitoring essential"))

# Breach concentration in sector
if len(sector_breach.filter(pl.col('breach_rate') > 50)) > 0:
    worst_sector = sector_breach.filter(pl.col('breach_rate') > 50).row(0, named=True)
    actions.append(("🟡 MONITOR", f"{worst_sector['sector']} sector has {worst_sector['breach_rate']:.1f}% breach rate - sector review warranted"))

if not actions:
    st.success("✅ No urgent covenant issues - portfolio is well within covenant limits")
else:
    for severity, action in actions:
        st.warning(f"{severity}: {action}")

# ==================== EXPORT ====================

st.subheader("Export Covenant Analysis")

col1, col2 = st.columns(2)

with col1:
    # Export breach details
    csv_data = breach_detail.write_csv() if len(filtered_df) > 0 else ""
    if csv_data:
        st.download_button(
            label="📥 Download Breach Details (CSV)",
            data=csv_data,
            file_name=f"covenant_breaches_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    st.write("**Covenant Summary:**")
    st.write(f"- Total Loans: {total_loans}")
    st.write(f"- Compliant: {compliant} ({compliance_pct:.1f}%)")
    st.write(f"- Breaches: {total_breaches} ({(total_breaches/total_loans)*100:.1f}%)")
    st.write(f"- Multiple Breaches: {multiple_breaches}")

st.info("💡 **Note:** Covenant thresholds can be adjusted above. Regular monitoring prevents breaches from escalating. D/E = Debt-to-Equity, IC = Interest Coverage.")
