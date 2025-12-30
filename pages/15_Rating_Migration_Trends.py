import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Rating Migration Trends", layout="wide")

st.title("Credit Rating Migration Analysis")
st.markdown("### Track Rating Changes & Transition Patterns")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# Load rating history
try:
    rating_history = pl.read_csv('data/rating_history.csv')
    rating_history = rating_history.with_columns([
        pl.col('snapshot_date').str.strptime(pl.Date, '%Y-%m-%d')
    ])
except Exception as e:
    st.error(f"Error loading rating history: {e}")
    st.info("Please ensure data/rating_history.csv exists")
    st.stop()

# ==================== MIGRATION SUMMARY ====================

st.subheader("Rating Migration Overview")

# Get latest two snapshots for each loan to determine direction
latest_ratings = rating_history.sort(['loan_id', 'snapshot_date'], descending=[False, True])
latest_two = latest_ratings.group_by('loan_id').head(2)

# Define rating order (higher index = worse rating)
rating_order = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC', 'C', 'D']
rating_rank = {rating: idx for idx, rating in enumerate(rating_order)}

# Determine migration direction
migration_data = []
for loan_id in latest_two['loan_id'].unique():
    loan_history = latest_two.filter(pl.col('loan_id') == loan_id).sort('snapshot_date', descending=True)
    
    if len(loan_history) == 2:
        latest = loan_history.row(0, named=True)
        previous = loan_history.row(1, named=True)
        
        latest_rank = rating_rank.get(latest['credit_rating'], -1)
        previous_rank = rating_rank.get(previous['credit_rating'], -1)
        
        if latest_rank < previous_rank:
            direction = 'Upgrade'
        elif latest_rank > previous_rank:
            direction = 'Downgrade'
        else:
            direction = 'Stable'
        
        migration_data.append({
            'loan_id': loan_id,
            'previous_rating': previous['credit_rating'],
            'current_rating': latest['credit_rating'],
            'direction': direction,
            'previous_date': previous['snapshot_date'],
            'current_date': latest['snapshot_date']
        })

migration_df = pl.DataFrame(migration_data)

# Join with portfolio for additional context
migration_full = migration_df.join(
    df.select(['loan_id', 'borrower', 'amount', 'sector', 'status']),
    on='loan_id',
    how='left'
)

# Calculate summary metrics
total_migrations = len(migration_df)
upgrades = len(migration_df.filter(pl.col('direction') == 'Upgrade'))
downgrades = len(migration_df.filter(pl.col('direction') == 'Downgrade'))
stable = len(migration_df.filter(pl.col('direction') == 'Stable'))

upgrade_pct = (upgrades / total_migrations * 100) if total_migrations > 0 else 0
downgrade_pct = (downgrades / total_migrations * 100) if total_migrations > 0 else 0
stable_pct = (stable / total_migrations * 100) if total_migrations > 0 else 0

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Upgrades",
        upgrades,
        delta=f"{upgrade_pct:.1f}% of portfolio",
        delta_color="normal"
    )

with col2:
    st.metric(
        "Downgrades",
        downgrades,
        delta=f"{downgrade_pct:.1f}% of portfolio",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "Stable Ratings",
        stable,
        delta=f"{stable_pct:.1f}% of portfolio",
        delta_color="off"
    )

with col4:
    net_migration = upgrades - downgrades
    st.metric(
        "Net Migration",
        net_migration,
        help="Upgrades minus Downgrades (positive = improving)"
    )

# ==================== MIGRATION FLOW ====================

st.subheader("Rating Migration Patterns")

col1, col2 = st.columns([3, 1])

with col1:
    # Create migration flow chart
    migration_summary = pl.DataFrame({
        'Direction': ['Upgrades', 'Downgrades', 'Stable'],
        'Count': [upgrades, downgrades, stable],
        'Color': ['#28a745', '#dc3545', '#6c757d']
    })
    
    fig_flow = go.Figure(data=[go.Bar(
        x=migration_summary['Direction'].to_list(),
        y=migration_summary['Count'].to_list(),
        text=migration_summary['Count'].to_list(),
        textposition='outside',
        marker_color=migration_summary['Color'].to_list()
    )])
    
    fig_flow.update_layout(
        title='Rating Migration Distribution',
        xaxis_title='Migration Type',
        yaxis_title='Number of Loans',
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig_flow, width=800)

with col2:
    st.write("**Migration Analysis**")
    st.write("")
    
    if upgrade_pct > downgrade_pct:
        st.success(f"✅ Portfolio quality improving: {upgrades} upgrades vs {downgrades} downgrades")
    elif downgrade_pct > upgrade_pct:
        st.warning(f"⚠️ Portfolio deteriorating: {downgrades} downgrades vs {upgrades} upgrades")
    else:
        st.info("ℹ️ Portfolio quality stable")
    
    st.write("")
    st.write(f"**Upgrade Rate:** {upgrade_pct:.1f}%")
    st.write(f"**Downgrade Rate:** {downgrade_pct:.1f}%")
    st.write(f"**Stability Rate:** {stable_pct:.1f}%")

# ==================== TRANSITION MATRIX ====================

st.subheader("Rating Transition Matrix")

# Build transition matrix
transitions = []
for row in migration_data:
    transitions.append({
        'from': row['previous_rating'],
        'to': row['current_rating']
    })

transition_df = pl.DataFrame(transitions)

# Create matrix
matrix_data = []
for from_rating in rating_order:
    row = {'Rating': from_rating}
    for to_rating in rating_order:
        count = len(transition_df.filter(
            (pl.col('from') == from_rating) & (pl.col('to') == to_rating)
        ))
        row[to_rating] = count
    matrix_data.append(row)

matrix_df = pl.DataFrame(matrix_data)

# Display as heatmap
fig_matrix = px.imshow(
    matrix_df.select(rating_order).to_numpy(),
    labels=dict(x="To Rating", y="From Rating", color="Transitions"),
    x=rating_order,
    y=rating_order,
    color_continuous_scale='YlOrRd',
    title='Rating Transition Matrix (Latest Period)',
    text_auto=True
)
fig_matrix.update_layout(height=500)
st.plotly_chart(fig_matrix, use_container_width=True)

st.info("💡 **How to read:** Rows = previous rating, Columns = current rating. Diagonal = stable ratings, above diagonal = upgrades, below diagonal = downgrades")

# ==================== MIGRATION TIMELINE ====================

st.subheader("Migration Timeline")

# Count migrations over time
timeline_data = []
all_dates = sorted(rating_history['snapshot_date'].unique().to_list())

for i in range(1, len(all_dates)):
    prev_date = all_dates[i-1]
    curr_date = all_dates[i]
    
    prev_snapshot = rating_history.filter(pl.col('snapshot_date') == prev_date)
    curr_snapshot = rating_history.filter(pl.col('snapshot_date') == curr_date)
    
    joined = prev_snapshot.join(curr_snapshot, on='loan_id', suffix='_curr')
    
    period_upgrades = 0
    period_downgrades = 0
    period_stable = 0
    
    for _, loan in joined.to_pandas().iterrows():
        prev_rank = rating_rank.get(loan['credit_rating'], -1)
        curr_rank = rating_rank.get(loan['credit_rating_curr'], -1)
        
        if curr_rank < prev_rank:
            period_upgrades += 1
        elif curr_rank > prev_rank:
            period_downgrades += 1
        else:
            period_stable += 1
    
    timeline_data.append({
        'period_end': curr_date,
        'upgrades': period_upgrades,
        'downgrades': period_downgrades,
        'stable': period_stable
    })

timeline_df = pl.DataFrame(timeline_data)

# Plot timeline
fig_timeline = go.Figure()

fig_timeline.add_trace(go.Scatter(
    x=timeline_df['period_end'].to_list(),
    y=timeline_df['upgrades'].to_list(),
    mode='lines+markers',
    name='Upgrades',
    line=dict(color='#28a745', width=2),
    marker=dict(size=8)
))

fig_timeline.add_trace(go.Scatter(
    x=timeline_df['period_end'].to_list(),
    y=timeline_df['downgrades'].to_list(),
    mode='lines+markers',
    name='Downgrades',
    line=dict(color='#dc3545', width=2),
    marker=dict(size=8)
))

fig_timeline.update_layout(
    title='Rating Migrations Over Time',
    xaxis_title='Period',
    yaxis_title='Number of Migrations',
    height=400,
    hovermode='x unified'
)

st.plotly_chart(fig_timeline, use_container_width=True)

# ==================== MIGRATION DETAILS ====================

st.subheader("Detailed Migration Analysis")

# Filter options
col1, col2, col3 = st.columns(3)

with col1:
    direction_filter = st.selectbox(
        "Migration Direction",
        options=['All', 'Upgrades', 'Downgrades', 'Stable']
    )

with col2:
    sector_filter = st.multiselect(
        "Filter by Sector",
        options=sorted(migration_full['sector'].unique().to_list()),
        default=None
    )

with col3:
    min_amount = st.number_input(
        "Min Loan Amount (£M)",
        min_value=0.0,
        max_value=float(migration_full['amount'].max()) / 1e6,
        value=0.0,
        step=1.0
    )

# Apply filters
filtered_migrations = migration_full

if direction_filter != 'All':
    filtered_migrations = filtered_migrations.filter(pl.col('direction') == direction_filter)

if sector_filter:
    filtered_migrations = filtered_migrations.filter(pl.col('sector').is_in(sector_filter))

if min_amount > 0:
    filtered_migrations = filtered_migrations.filter(pl.col('amount') >= min_amount * 1e6)

# Display migration details
if len(filtered_migrations) > 0:
    st.write(f"**Showing {len(filtered_migrations)} migrations**")
    
    display_migrations = filtered_migrations.select([
        'loan_id',
        'borrower',
        'amount',
        'sector',
        'previous_rating',
        'current_rating',
        'direction',
        'status'
    ]).sort('amount', descending=True)
    
    # Format for display
    display_df = display_migrations.to_pandas()
    display_df['amount'] = display_df['amount'].apply(lambda x: f"£{x/1e6:.2f}M")
    
    # Add direction emoji
    direction_map = {'Upgrade': '📈', 'Downgrade': '📉', 'Stable': '➡️'}
    display_df['direction'] = display_df['direction'].apply(lambda x: f"{direction_map.get(x, '')} {x}")
    
    display_df.columns = ['Loan ID', 'Borrower', 'Amount', 'Sector', 'Previous', 'Current', 'Direction', 'Status']
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=400
    )
else:
    st.info("No migrations match the selected filters")

# ==================== SECTOR & NOTCH ANALYSIS ====================

st.subheader("Migration Patterns by Segment")

col1, col2 = st.columns(2)

with col1:
    # Migration by sector
    sector_migration = migration_full.group_by('sector').agg([
        pl.col('loan_id').count().alias('total'),
        (pl.col('direction') == 'Upgrade').sum().alias('upgrades'),
        (pl.col('direction') == 'Downgrade').sum().alias('downgrades')
    ]).with_columns([
        (pl.col('upgrades') - pl.col('downgrades')).alias('net_migration')
    ]).sort('net_migration', descending=True)
    
    fig_sector = go.Figure()
    fig_sector.add_trace(go.Bar(
        x=sector_migration['sector'].to_list(),
        y=sector_migration['upgrades'].to_list(),
        name='Upgrades',
        marker_color='#28a745'
    ))
    fig_sector.add_trace(go.Bar(
        x=sector_migration['sector'].to_list(),
        y=sector_migration['downgrades'].to_list(),
        name='Downgrades',
        marker_color='#dc3545'
    ))
    
    fig_sector.update_layout(
        title='Migrations by Sector',
        xaxis_title='Sector',
        yaxis_title='Count',
        barmode='group',
        height=400,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_sector, width=600)

with col2:
    # Calculate notch changes (rating steps)
    notch_changes = []
    for row in migration_data:
        from_rank = rating_rank.get(row['previous_rating'], -1)
        to_rank = rating_rank.get(row['current_rating'], -1)
        notch_change = to_rank - from_rank
        
        if notch_change != 0:
            notch_changes.append(notch_change)
    
    if notch_changes:
        notch_df = pl.DataFrame({'notch_change': notch_changes})
        
        fig_notch = px.histogram(
            notch_df.to_dicts(),
            x='notch_change',
            nbins=15,
            title='Rating Notch Changes',
            labels={'notch_change': 'Notch Change (negative = upgrade)', 'count': 'Frequency'},
            color_discrete_sequence=['#6c757d']
        )
        fig_notch.add_vline(x=0, line_dash="dash", line_color="black")
        fig_notch.update_layout(height=400)
        st.plotly_chart(fig_notch, width=600)
    else:
        st.info("No rating changes to display")

# ==================== KEY INSIGHTS ====================

st.subheader("Key Migration Insights")

insights = []

# Major downgrades
major_downgrades = [n for n in notch_changes if n >= 3]
if major_downgrades:
    insights.append(("🔴 ALERT", f"{len(major_downgrades)} loans downgraded by 3+ notches - significant credit deterioration"))

# Investment grade to speculative
ig_ratings = ['AAA', 'AA', 'A', 'BBB']
fallen_angels = migration_full.filter(
    pl.col('previous_rating').is_in(ig_ratings) & 
    ~pl.col('current_rating').is_in(ig_ratings)
)
if len(fallen_angels) > 0:
    fallen_exp = fallen_angels.select(pl.col('amount').sum()).item()
    insights.append(("🟠 WARNING", f"{len(fallen_angels)} 'fallen angels' (investment → speculative grade) totaling £{fallen_exp/1e6:.1f}M"))

# Rising stars
rising_stars = migration_full.filter(
    ~pl.col('previous_rating').is_in(ig_ratings) & 
    pl.col('current_rating').is_in(ig_ratings)
)
if len(rising_stars) > 0:
    insights.append(("🟢 POSITIVE", f"{len(rising_stars)} 'rising stars' upgraded to investment grade"))

# Sector trends
worst_sector = sector_migration.sort('net_migration').row(0, named=True)
if worst_sector['net_migration'] < -2:
    insights.append(("🟡 MONITOR", f"{worst_sector['sector']} sector showing negative migration trend (net {worst_sector['net_migration']})"))

if not insights:
    st.success("✅ No significant migration concerns - rating changes are within normal patterns")
else:
    for severity, insight in insights:
        if severity.startswith("🔴"):
            st.error(f"{severity}: {insight}")
        elif severity.startswith("🟠"):
            st.warning(f"{severity}: {insight}")
        else:
            st.info(f"{severity}: {insight}")

# ==================== EXPORT ====================

st.subheader("Export Migration Data")

col1, col2 = st.columns(2)

with col1:
    csv_data = filtered_migrations.write_csv() if len(filtered_migrations) > 0 else ""
    if csv_data:
        st.download_button(
            label="📥 Download Migration Details (CSV)",
            data=csv_data,
            file_name=f"rating_migrations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    st.write("**Migration Summary:**")
    st.write(f"- Total Analyzed: {total_migrations}")
    st.write(f"- Upgrades: {upgrades} ({upgrade_pct:.1f}%)")
    st.write(f"- Downgrades: {downgrades} ({downgrade_pct:.1f}%)")
    st.write(f"- Stable: {stable} ({stable_pct:.1f}%)")

st.info("💡 **Note:** Migration analysis compares the two most recent rating snapshots. Monitor for fallen angels (IG→HY) and watch for sectors with negative net migration.")
