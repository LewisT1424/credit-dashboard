import streamlit as st
import polars as pl
from utils import get_borrower_detail
import plotly.graph_objects as go
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Portfolio Health Dashboard", layout="wide")

st.title("Portfolio Health Dashboard")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# ==================== CALCULATE HEALTH METRICS ====================

def calculate_health_score(df):
    """Calculate composite portfolio health score (0-100)"""
    total_loans = len(df)
    
    # 1. Performance Score (30%)
    performing = len(df.filter(pl.col('status') == 'Performing'))
    performance_score = (performing / total_loans) * 100
    
    # 2. Quality Score (30%) - based on credit ratings
    # A/BBB+ = 100%, BBB = 90%, BB+ = 70%, BB = 50%, BB- = 40%, B+ = 30%, B = 20%, lower = 10%
    rating_scores = {
        'A': 100, 'A-': 100,
        'BBB+': 90, 'BBB': 85, 'BBB-': 80,
        'BB+': 70, 'BB': 60, 'BB-': 50,
        'B+': 35, 'B': 25, 'B-': 20,
        'CCC+': 10, 'CCC': 5, 'D': 0
    }
    
    quality_score = 0
    for rating, score in rating_scores.items():
        count = len(df.filter(pl.col('credit_rating') == rating))
        quality_score += (count / total_loans) * score
    
    # 3. Concentration Score (25%) - HHI-based
    # Lower HHI = better diversification
    borrower_exposure = df.group_by('borrower').agg(pl.col('amount').sum()).sort('amount', descending=True)
    total_amount = df.select(pl.col('amount').sum()).item()
    
    concentration_ratio = (borrower_exposure['amount'] / total_amount) ** 2
    hhi = (concentration_ratio.sum()) * 10000
    
    # HHI scoring: <1500 = 100%, 1500-2500 = 80%, >2500 = 60%
    if hhi < 1500:
        concentration_score = 100
    elif hhi < 2500:
        concentration_score = 80
    else:
        concentration_score = 60
    
    # 4. Maturity Score (15%) - avoid concentration in near term
    from datetime import datetime
    today = datetime.now()
    
    near_term = len(df.filter(
        (pl.col('maturity_date').str.to_date() - pl.lit(today.date())).dt.total_days() <= 365
    ))
    maturity_score = max(0, 100 - (near_term / total_loans) * 50)
    
    # Weighted composite score
    health_score = (
        (performance_score * 0.30) +
        (quality_score * 0.30) +
        (concentration_score * 0.25) +
        (maturity_score * 0.15)
    )
    
    return round(health_score, 1), {
        'performance': round(performance_score, 1),
        'quality': round(quality_score, 1),
        'concentration': round(concentration_score, 1),
        'maturity': round(maturity_score, 1),
        'hhi': round(hhi, 1)
    }

# Calculate scores
overall_score, component_scores = calculate_health_score(df)

# ==================== DISPLAY HEALTH METRICS ====================

# Top row: Overall Health Score
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Gauge chart for overall health
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=overall_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Portfolio Health Score"},
        delta={'reference': 75, 'suffix': "pts"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkgreen" if overall_score >= 75 else "orange" if overall_score >= 50 else "darkred"},
            'steps': [
                {'range': [0, 50], 'color': "lightpink"},
                {'range': [50, 75], 'color': "lightyellow"},
                {'range': [75, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig_gauge.update_layout(height=300, width=600, margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_gauge, width=600)

with col2:
    st.metric("Health Status", "Healthy" if overall_score >= 75 else "Monitor" if overall_score >= 50 else "At Risk")
    st.metric("Portfolio Size", f"£{df.select(pl.col('amount').sum()).item()/1e6:.1f}M")

with col3:
    st.metric("Loan Count", len(df))
    st.metric("Borrowers", df.select('borrower').n_unique())

# Component Scores
st.subheader("Health Score Components")
col1, col2, col3, col4 = st.columns(4)

with col1:
    color = "green" if component_scores['performance'] >= 80 else "orange" if component_scores['performance'] >= 60 else "red"
    st.metric(
        "Performance Score",
        f"{component_scores['performance']:.0f}%",
        delta=f"{component_scores['performance'] - 80:.0f}% vs target",
        delta_color="off"
    )

with col2:
    color = "green" if component_scores['quality'] >= 75 else "orange" if component_scores['quality'] >= 50 else "red"
    st.metric(
        "Quality Score",
        f"{component_scores['quality']:.0f}%",
        delta=f"Rating mix"
    )

with col3:
    color = "green" if component_scores['concentration'] >= 80 else "orange" if component_scores['concentration'] >= 60 else "red"
    st.metric(
        "Concentration Score",
        f"{component_scores['concentration']:.0f}%",
        delta=f"HHI: {component_scores['hhi']:.0f}"
    )

with col4:
    color = "green" if component_scores['maturity'] >= 80 else "orange" if component_scores['maturity'] >= 50 else "red"
    st.metric(
        "Maturity Score",
        f"{component_scores['maturity']:.0f}%",
        delta="Spread across years"
    )

# ==================== RISK HEAT MAP ====================

st.subheader("Borrower Risk Heat Map")

# Create risk matrix
borrower_data = []
for borrower in df.select('borrower').unique()['borrower'].to_list():
    borrower_df = df.filter(pl.col('borrower') == borrower)
    
    # Get borrower details
    detail = get_borrower_detail(df, borrower)
    
    if detail:
        # Risk calculation
        exposure_pct = (detail['total_exposure'] / df.select(pl.col('amount').sum()).item()) * 100
        
        # Credit quality (1-5, 1=best)
        avg_rating = borrower_df.select('credit_rating').to_series().to_list()
        rating_scores_list = [
            {'A': 1, 'A-': 1, 'BBB+': 2, 'BBB': 2, 'BBB-': 2, 'BB+': 3, 'BB': 3, 'BB-': 3,
             'B+': 4, 'B': 4, 'B-': 4, 'CCC+': 5, 'CCC': 5, 'D': 5}.get(r, 3)
            for r in avg_rating
        ]
        quality_score = sum(rating_scores_list) / len(rating_scores_list) if rating_scores_list else 3
        
        # Performance (1-5, 1=best)
        performing_loans = len(borrower_df.filter(pl.col('status') == 'Performing'))
        performance_pct = (performing_loans / len(borrower_df)) * 100
        performance_score = 1 if performance_pct >= 95 else 2 if performance_pct >= 80 else 3 if performance_pct >= 60 else 4 if performance_pct >= 40 else 5
        
        # Overall risk score (1-5)
        risk_score = (quality_score + performance_score) / 2
        
        borrower_data.append({
            'borrower': borrower,
            'exposure_pct': exposure_pct,
            'quality_score': quality_score,
            'performance_score': performance_score,
            'risk_score': risk_score,
            'loan_count': len(borrower_df),
            'performing': performing_loans
        })

borrower_risk_df = pl.DataFrame(borrower_data).sort('risk_score', descending=True)

# Heat map visualization
fig_heatmap = px.scatter(
    borrower_risk_df.to_dicts(),
    x='quality_score',
    y='performance_score',
    size='exposure_pct',
    color='risk_score',
    hover_data={'borrower': True, 'exposure_pct': ':.2f', 'loan_count': True, 'performing': True},
    color_continuous_scale='RdYlGn_r',
    title='Borrower Risk Heat Map (Size = Exposure %)',
    labels={'quality_score': 'Credit Quality Score', 'performance_score': 'Performance Score'}
)
fig_heatmap.update_layout(height=500, width=1200)
st.plotly_chart(fig_heatmap, width=1200)

# ==================== KEY RISK DRIVERS ====================

st.subheader("Key Risk Drivers")

col1, col2 = st.columns(2)

with col1:
    st.write("**Top Risk Exposures**")
    
    top_borrowers = borrower_risk_df.head(5)
    risk_list = []
    
    for row in top_borrowers.to_dicts():
        risk_color = "🔴" if row['risk_score'] >= 3.5 else "🟠" if row['risk_score'] >= 2.5 else "🟡"
        risk_list.append(f"{risk_color} {row['borrower']}: {row['exposure_pct']:.1f}% | {row['loan_count']} loans")
    
    for risk in risk_list:
        st.write(risk)

with col2:
    st.write("**Problem Loans by Status**")
    
    status_counts = df.group_by('status').agg(
        pl.col('loan_id').count().alias('count'),
        pl.col('amount').sum().alias('total_exposure')
    ).sort('total_exposure', descending=True)
    
    for row in status_counts.to_dicts():
        status = row['status']
        count = row['count']
        exposure = row['total_exposure'] / 1e6
        
        status_icon = "✅" if status == "Performing" else "⚠️" if status == "Watch List" else "❌"
        st.write(f"{status_icon} {status}: {count} loans | £{exposure:.1f}M")

# ==================== RATING DISTRIBUTION ====================

st.subheader("Credit Rating Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    rating_dist = df.group_by('credit_rating').agg(
        pl.col('loan_id').count().alias('count'),
        pl.col('amount').sum().alias('exposure')
    )
    
    # Define rating order for proper sorting
    rating_order = ['A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC', 'D']
    rating_data = []
    
    for rating in rating_order:
        filtered = df.filter(pl.col('credit_rating') == rating)
        if len(filtered) > 0:
            rating_data.append({
                'rating': rating,
                'count': len(filtered),
                'exposure': filtered.select(pl.col('amount').sum()).item()
            })
    
    if rating_data:
        rating_df = pl.DataFrame(rating_data)
        
        fig_rating = px.bar(
            rating_df.to_dicts(),
            x='rating',
            y='count',
            color='exposure',
            color_continuous_scale='RdYlGn_r',
            title='Loans by Credit Rating',
            labels={'count': 'Number of Loans', 'exposure': 'Exposure (£)'}
        )
        fig_rating.update_layout(height=400, width=800)
        st.plotly_chart(fig_rating, width=800)

with col2:
    st.write("**Rating Summary**")
    
    investment_grade = len(df.filter(pl.col('credit_rating').is_in(['A', 'A-', 'BBB+', 'BBB', 'BBB-'])))
    upper_spec = len(df.filter(pl.col('credit_rating').is_in(['BB+', 'BB', 'BB-'])))
    lower_spec = len(df.filter(pl.col('credit_rating').is_in(['B+', 'B', 'B-', 'CCC+', 'CCC', 'D'])))
    
    st.metric("Investment Grade", f"{investment_grade} loans ({investment_grade/len(df)*100:.0f}%)")
    st.metric("Upper Spec Grade", f"{upper_spec} loans ({upper_spec/len(df)*100:.0f}%)")
    st.metric("Lower Spec/Def", f"{lower_spec} loans ({lower_spec/len(df)*100:.0f}%)")

# ==================== ALERTS & RECOMMENDATIONS ====================

st.subheader("Alerts & Recommendations")

alerts = []

# Alert 1: Overall health
if overall_score < 50:
    alerts.append(("🔴 CRITICAL", "Portfolio health score is critically low. Immediate action required."))
elif overall_score < 75:
    alerts.append(("🟠 WARNING", "Portfolio health score is below optimal. Review concentration and performance."))

# Alert 2: Problem loans
problem_loans = df.filter(pl.col('status') != 'Performing')
if len(problem_loans) > 0:
    problem_pct = (len(problem_loans) / len(df)) * 100
    alerts.append(("⚠️ ISSUE", f"{len(problem_loans)} non-performing loans ({problem_pct:.1f}% of portfolio)"))

# Alert 3: Concentration
if component_scores['concentration'] < 70:
    alerts.append(("⚠️ ISSUE", f"High borrower concentration (HHI: {component_scores['hhi']:.0f}). Consider diversification."))

# Alert 4: Maturity
if component_scores['maturity'] < 70:
    alerts.append(("🟡 MONITOR", "Significant maturity concentration in next 12 months. Monitor refinancing risk."))

# Alert 5: Quality
if component_scores['quality'] < 60:
    alerts.append(("🟡 MONITOR", "Portfolio contains significant speculative-grade exposure. Enhanced monitoring recommended."))

if alerts:
    for icon_status, message in alerts:
        st.warning(f"{icon_status}: {message}")
else:
    st.success("✅ No major alerts. Portfolio appears healthy.")

# ==================== SUMMARY STATISTICS ====================

st.subheader("Portfolio Summary")

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric("Total Exposure", f"£{df.select(pl.col('amount').sum()).item()/1e6:.1f}M")

with summary_col2:
    avg_rate = df.select(pl.col('rate').mean()).item()
    st.metric("Avg Interest Rate", f"{avg_rate:.2f}%")

with summary_col3:
    weighted_exposure = (
        df.select(
            (pl.col('amount') * pl.col('rate') / 100).sum() / pl.col('amount').sum()
        ).item()
    )
    st.metric("Weighted Avg Rate", f"{weighted_exposure:.2f}%")

with summary_col4:
    sector_count = df.select('sector').n_unique()
    st.metric("Sector Diversity", f"{sector_count} sectors")
