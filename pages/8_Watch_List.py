import streamlit as st
import polars as pl
from utils import get_borrower_detail
import plotly.graph_objects as go
import plotly.express as px
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Watch List Management", layout="wide")

st.title("Watch List Management")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# Filter to watch list only
watch_list_df = df.filter(pl.col('status') == 'Watch List')

# ==================== SUMMARY METRICS ====================

st.subheader("Watch List Summary")

if len(watch_list_df) == 0:
    st.success("✅ No loans on watch list. Portfolio is performing well!")
else:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_watch = len(watch_list_df)
    watch_exposure = watch_list_df.select(pl.col('amount').sum()).item()
    total_exposure = df.select(pl.col('amount').sum()).item()
    watch_pct = (watch_exposure / total_exposure) * 100
    
    with col1:
        st.metric("Watch List Loans", total_watch)
    
    with col2:
        st.metric("Watch List Exposure", f"£{watch_exposure/1e6:.1f}M")
    
    with col3:
        st.metric("% of Portfolio", f"{watch_pct:.1f}%")
    
    with col4:
        avg_rate = watch_list_df.select(pl.col('rate').mean()).item()
        st.metric("Avg Interest Rate", f"{avg_rate:.2f}%")
    
    with col5:
        avg_rating = watch_list_df.select(pl.col('credit_rating').n_unique()).item()
        st.metric("Unique Borrowers", watch_list_df.select('borrower').n_unique())
    
    # ==================== WATCH LIST TABLE ====================
    
    st.subheader("Watch List Loans")
    
    watch_display = watch_list_df.select([
        'loan_id',
        'borrower',
        'amount',
        'rate',
        'credit_rating',
        'sector',
        'maturity_date'
    ]).with_columns([
        (pl.col('amount') / 1e6).alias('Amount (M)')
    ]).drop(['amount']).sort('credit_rating', descending=True)
    
    st.dataframe(watch_display, width=1200, height=400)
    
    # ==================== CREDIT RATING ANALYSIS ====================
    
    st.subheader("Watch List by Credit Rating")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        rating_dist = watch_list_df.group_by('credit_rating').agg(
            pl.col('loan_id').count().alias('count'),
            pl.col('amount').sum().alias('exposure')
        )
        
        if len(rating_dist) > 0:
            fig_rating = px.bar(
                rating_dist.to_dicts(),
                x='credit_rating',
                y='count',
                color='exposure',
                color_continuous_scale='Reds',
                title='Watch List Distribution by Rating',
                labels={'count': 'Number of Loans', 'exposure': 'Exposure (£)', 'credit_rating': 'Credit Rating'}
            )
            fig_rating.update_layout(height=400, width=800)
            st.plotly_chart(fig_rating, width=1000)
    
    with col2:
        st.write("**Rating Breakdown**")
        
        speculative = len(watch_list_df.filter(pl.col('credit_rating').is_in(['B+', 'B', 'B-', 'CCC+', 'CCC'])))
        upper_spec = len(watch_list_df.filter(pl.col('credit_rating').is_in(['BB+', 'BB', 'BB-'])))
        investment = len(watch_list_df.filter(pl.col('credit_rating').is_in(['A', 'A-', 'BBB+', 'BBB', 'BBB-'])))
        
        st.metric("Investment Grade", f"{investment} loans")
        st.metric("Upper Speculative", f"{upper_spec} loans")
        st.metric("Lower Speculative", f"{speculative} loans")
    
    # ==================== SECTOR ANALYSIS ====================
    
    st.subheader("Watch List by Sector")
    
    sector_dist = watch_list_df.group_by('sector').agg(
        pl.col('loan_id').count().alias('count'),
        pl.col('amount').sum().alias('exposure')
    ).sort('exposure', descending=True)
    
    if len(sector_dist) > 0:
        fig_sector = px.pie(
            sector_dist.to_dicts(),
            values='exposure',
            names='sector',
            title='Watch List Exposure by Sector',
            hole=0.3
        )
        fig_sector.update_layout(height=450, width=1000)
        st.plotly_chart(fig_sector, width=1200)
    
    # ==================== MATURITY ANALYSIS ====================
    
    st.subheader("Watch List Maturity Profile")
    
    today = datetime.now().date()
    
    watch_with_days = watch_list_df.with_columns([
        (pl.col('maturity_date').str.to_date() - pl.lit(today)).dt.total_days().alias('days_to_maturity')
    ])
    
    # Categorize by time to maturity
    maturity_buckets = []
    
    # < 6 months
    lt_6m = len(watch_with_days.filter(pl.col('days_to_maturity') < 180))
    lt_6m_exp = watch_with_days.filter(pl.col('days_to_maturity') < 180).select(pl.col('amount').sum()).item() or 0
    maturity_buckets.append({'bucket': '< 6 months', 'count': lt_6m, 'exposure': lt_6m_exp})
    
    # 6-12 months
    m6_12 = len(watch_with_days.filter((pl.col('days_to_maturity') >= 180) & (pl.col('days_to_maturity') < 365)))
    m6_12_exp = watch_with_days.filter((pl.col('days_to_maturity') >= 180) & (pl.col('days_to_maturity') < 365)).select(pl.col('amount').sum()).item() or 0
    maturity_buckets.append({'bucket': '6-12 months', 'count': m6_12, 'exposure': m6_12_exp})
    
    # 1-2 years
    y1_2 = len(watch_with_days.filter((pl.col('days_to_maturity') >= 365) & (pl.col('days_to_maturity') < 730)))
    y1_2_exp = watch_with_days.filter((pl.col('days_to_maturity') >= 365) & (pl.col('days_to_maturity') < 730)).select(pl.col('amount').sum()).item() or 0
    maturity_buckets.append({'bucket': '1-2 years', 'count': y1_2, 'exposure': y1_2_exp})
    
    # > 2 years
    gt_2y = len(watch_with_days.filter(pl.col('days_to_maturity') >= 730))
    gt_2y_exp = watch_with_days.filter(pl.col('days_to_maturity') >= 730).select(pl.col('amount').sum()).item() or 0
    maturity_buckets.append({'bucket': '> 2 years', 'count': gt_2y, 'exposure': gt_2y_exp})
    
    maturity_df = pl.DataFrame(maturity_buckets)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_maturity = px.bar(
            maturity_df.to_dicts(),
            x='bucket',
            y='count',
            color='exposure',
            color_continuous_scale='Oranges',
            title='Watch List Maturity Distribution',
            labels={'count': 'Number of Loans', 'exposure': 'Exposure (£)', 'bucket': 'Time to Maturity'}
        )
        fig_maturity.update_layout(height=400, width=800)
        st.plotly_chart(fig_maturity, width=1200)
    
    with col2:
        st.write("**Refinancing Risk**")
        
        if lt_6m > 0:
            st.warning(f"🔴 {lt_6m} loans maturing in < 6 months (£{lt_6m_exp/1e6:.1f}M)")
        if m6_12 > 0:
            st.warning(f"🟠 {m6_12} loans maturing in 6-12 months (£{m6_12_exp/1e6:.1f}M)")
        
        st.info(f"Total refinancing risk: £{(lt_6m_exp + m6_12_exp)/1e6:.1f}M in next 12 months")
    
    # ==================== BORROWER DRILL-DOWN ====================
    
    st.subheader("Watch List Borrower Details")
    
    watch_borrowers = sorted(watch_list_df.select('borrower').unique()['borrower'].to_list())
    selected_borrower = st.selectbox(
        "Select a borrower to view details",
        watch_borrowers,
        key="watch_list_borrower"
    )
    
    if selected_borrower:
        borrower_watch = watch_list_df.filter(pl.col('borrower') == selected_borrower)
        detail = get_borrower_detail(df, selected_borrower)
        
        if detail:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Exposure",
                    f"£{detail['total_exposure']/1e6:.2f}M",
                    delta=f"{detail['pct_of_portfolio']:.2f}% of portfolio"
                )
            
            with col2:
                st.metric(
                    "Watch List Loans",
                    len(borrower_watch)
                )
            
            with col3:
                st.metric(
                    "Avg Interest Rate",
                    f"{detail['avg_rate']:.2f}%"
                )
            
            with col4:
                performing = len(detail['loans'].filter(pl.col('status') == 'Performing'))
                health_pct = (performing / detail['num_loans']) * 100
                st.metric(
                    "Performing Loans",
                    f"{performing}/{detail['num_loans']}",
                    delta=f"{health_pct:.1f}%"
                )
            
            # Borrower's watch list loans
            st.write("**Watch List Loans for This Borrower**")
            
            watch_detail = borrower_watch.select([
                'loan_id',
                'amount',
                'rate',
                'credit_rating',
                'sector',
                'maturity_date'
            ]).with_columns([
                (pl.col('amount') / 1e6).alias('Amount (M)')
            ]).drop(['amount'])
            
            st.dataframe(watch_detail, width=1200)
            
            # Risk indicators for this borrower's watch list
            st.write("**Risk Indicators**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                high_risk = len(borrower_watch.filter(pl.col('credit_rating').is_in(['D', 'C', 'B', 'B-'])))
                if high_risk > 0:
                    st.warning(f"High Risk Rating: {high_risk} loans")
                else:
                    st.success("No critically rated loans")
            
            with col2:
                near_maturity = len(borrower_watch.with_columns([
                    (pl.col('maturity_date').str.to_date() - pl.lit(today)).dt.total_days().alias('days_left')
                ]).filter(pl.col('days_left') < 180))
                
                if near_maturity > 0:
                    st.warning(f"Near Maturity: {near_maturity} loans in < 6 months")
                else:
                    st.success("Adequate maturity spread")
            
            with col3:
                avg_rating = borrower_watch.select('credit_rating').n_unique()
                st.info(f"Rating Diversity: {avg_rating} different ratings")
    
    # ==================== ACTION ITEMS ====================
    
    st.subheader("Recommended Actions")
    
    actions = []
    
    # Action 1: Near-term maturities
    if lt_6m > 0:
        actions.append(("🔴 URGENT", f"Refinance {lt_6m} loans maturing in < 6 months (£{lt_6m_exp/1e6:.1f}M)"))
    
    # Action 2: High concentration
    if watch_pct > 15:
        actions.append(("🟠 PRIORITY", f"Watch List represents {watch_pct:.1f}% of portfolio - monitor concentration"))
    
    # Action 3: Low rated loans
    low_rated = len(watch_list_df.filter(pl.col('credit_rating').is_in(['B', 'B-', 'CCC+', 'CCC'])))
    if low_rated > 0:
        actions.append(("🟠 PRIORITY", f"Monitor {low_rated} speculative-grade loans for deterioration"))
    
    # Action 4: Borrower concentration
    top_borrower = watch_list_df.group_by('borrower').agg(
        pl.col('amount').sum().alias('total')
    ).sort('total', descending=True).row(0, named=True) if len(watch_list_df) > 0 else None
    
    if top_borrower:
        top_borrow_exp = (top_borrower['total'] / watch_exposure) * 100
        if top_borrow_exp > 30:
            actions.append(("🟡 MONITOR", f"Top borrower ({top_borrower['borrower']}) represents {top_borrow_exp:.1f}% of watch list"))
    
    if actions:
        for severity, action in actions:
            st.warning(f"{severity}: {action}")
    else:
        st.success("✅ All watch list loans are being appropriately monitored")
    
    # ==================== TREND ANALYSIS ====================
    
    st.subheader("Watch List Trends")
    
    trend_col1, trend_col2 = st.columns(2)
    
    with trend_col1:
        st.write("**Watch List Size Over Scenarios**")
        
        # Simple scenario view - this would track historical data
        current_watch = len(watch_list_df)
        
        trend_data = [
            {'scenario': 'Current', 'watch_list_count': current_watch},
            {'scenario': 'If +5% Default', 'watch_list_count': current_watch + int(current_watch * 0.05)},
            {'scenario': 'If -5% Default', 'watch_list_count': max(0, current_watch - int(current_watch * 0.05))},
        ]
        
        trend_df = pl.DataFrame(trend_data)
        
        fig_trend = px.bar(
            trend_df.to_dicts(),
            x='scenario',
            y='watch_list_count',
            color='watch_list_count',
            color_continuous_scale='Reds',
            title='Potential Watch List Growth Scenarios'
        )
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, width=1000)
    
    with trend_col2:
        st.write("**Watch List by Borrower**")
        
        borrower_watch_dist = watch_list_df.group_by('borrower').agg(
            pl.col('loan_id').count().alias('count'),
            pl.col('amount').sum().alias('exposure')
        ).sort('count', descending=True).head(8)
        
        if len(borrower_watch_dist) > 0:
            fig_borrow = px.bar(
                borrower_watch_dist.to_dicts(),
                x='count',
                y='borrower',
                color='exposure',
                color_continuous_scale='Reds',
                title='Top Borrowers on Watch List',
                orientation='h'
            )
            fig_borrow.update_layout(height=400)
            st.plotly_chart(fig_borrow, width=900)
