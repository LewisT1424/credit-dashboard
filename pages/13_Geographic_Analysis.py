import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Geographic Analysis", layout="wide")

st.title("Geographic Portfolio Analysis")
st.markdown("### Regional Exposure & Risk Distribution")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# ==================== GEOGRAPHIC OVERVIEW ====================

st.subheader("Geographic Distribution")

# Calculate country-level metrics
country_stats = df.group_by('country').agg([
    pl.col('loan_id').count().alias('loan_count'),
    pl.col('amount').sum().alias('total_exposure'),
    pl.col('rate').mean().alias('avg_rate'),
    pl.col('borrower').n_unique().alias('unique_borrowers')
]).with_columns([
    (pl.col('total_exposure') / df.select(pl.col('amount').sum()).item() * 100).alias('portfolio_pct')
]).sort('total_exposure', descending=True)

# Display top metrics
col1, col2, col3, col4 = st.columns(4)

total_countries = country_stats.height
total_exposure = df.select(pl.col('amount').sum()).item()

with col1:
    st.metric(
        "Countries",
        total_countries,
        help="Number of countries in portfolio"
    )

with col2:
    top_country = country_stats.row(0, named=True)
    st.metric(
        "Top Country",
        top_country['country'],
        delta=f"£{top_country['total_exposure']/1e6:.1f}M ({top_country['portfolio_pct']:.1f}%)"
    )

with col3:
    # HHI for geographic concentration
    hhi = country_stats.select(
        ((pl.col('portfolio_pct') ** 2).sum())
    ).item()
    
    hhi_status = "Low" if hhi < 1500 else "Moderate" if hhi < 2500 else "High"
    st.metric(
        "Geographic HHI",
        f"{hhi:.0f}",
        delta=f"{hhi_status} concentration",
        delta_color="inverse" if hhi < 1500 else "off"
    )

with col4:
    avg_country_exposure = country_stats.select(pl.col('total_exposure').mean()).item()
    st.metric(
        "Avg per Country",
        f"£{avg_country_exposure/1e6:.1f}M"
    )

# ==================== COUNTRY EXPOSURE MAP ====================

st.subheader("Portfolio Exposure by Country")

col1, col2 = st.columns([2, 1])

with col1:
    # Create choropleth-style bar chart (Plotly Express doesn't do maps without folium)
    # Using horizontal bar chart as geographic visualization
    
    fig_geo = px.bar(
        country_stats.to_dicts(),
        y='country',
        x='total_exposure',
        color='avg_rate',
        orientation='h',
        title='Exposure by Country',
        labels={'total_exposure': 'Total Exposure (£)', 'country': 'Country', 'avg_rate': 'Avg Rate (%)'},
        color_continuous_scale='RdYlGn_r',
        hover_data={'loan_count': True, 'unique_borrowers': True, 'portfolio_pct': ':.2f'}
    )
    fig_geo.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_geo, width=800)

with col2:
    st.write("**Country Statistics**")
    
    # Display table
    country_display = country_stats.select([
        'country',
        'loan_count',
        pl.col('total_exposure').map_elements(lambda x: f"£{x/1e6:.1f}M", return_dtype=pl.Utf8).alias('exposure'),
        pl.col('portfolio_pct').map_elements(lambda x: f"{x:.1f}%", return_dtype=pl.Utf8).alias('% portfolio')
    ])
    
    st.dataframe(
        country_display.to_pandas(),
        hide_index=True,
        use_container_width=True,
        height=450
    )

# ==================== RISK BY GEOGRAPHY ====================

st.subheader("Credit Quality by Region")

col1, col2 = st.columns(2)

with col1:
    # Rating distribution by country
    country_rating = df.group_by(['country', 'credit_rating']).agg([
        pl.col('amount').sum().alias('exposure')
    ])
    
    # Get top 8 countries by exposure
    top_countries = country_stats.head(8)['country'].to_list()
    
    country_rating_filtered = country_rating.filter(
        pl.col('country').is_in(top_countries)
    )
    
    fig_rating = px.bar(
        country_rating_filtered.to_dicts(),
        x='country',
        y='exposure',
        color='credit_rating',
        title='Credit Rating Distribution by Country (Top 8)',
        labels={'exposure': 'Exposure (£)', 'country': 'Country'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_rating.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_rating, width=600)

with col2:
    # Watch list by country
    watch_by_country = df.filter(
        pl.col('status').is_in(['Watch List', 'Defaulted'])
    ).group_by('country').agg([
        pl.col('loan_id').count().alias('problem_loans'),
        pl.col('amount').sum().alias('problem_exposure')
    ]).join(
        country_stats.select(['country', 'total_exposure']),
        on='country'
    ).with_columns([
        (pl.col('problem_exposure') / pl.col('total_exposure') * 100).alias('problem_pct')
    ]).sort('problem_pct', descending=True)
    
    if len(watch_by_country) > 0:
        fig_watch = px.bar(
            watch_by_country.to_dicts(),
            x='country',
            y='problem_pct',
            title='Problem Loans as % of Country Exposure',
            labels={'problem_pct': 'Problem Loans (%)', 'country': 'Country'},
            color='problem_pct',
            color_continuous_scale='Reds'
        )
        fig_watch.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_watch, width=600)
    else:
        st.info("No problem loans in portfolio")

# ==================== SECTOR BY GEOGRAPHY ====================

st.subheader("Sector Distribution by Country")

# Create heatmap of country vs sector
country_sector = df.group_by(['country', 'sector']).agg([
    pl.col('amount').sum().alias('exposure')
]).pivot(
    index='country',
    columns='sector',
    values='exposure'
)

# Convert to pandas for heatmap
country_sector_pd = country_sector.to_pandas().fillna(0)
country_sector_pd = country_sector_pd.set_index('country')

# Create heatmap
fig_heatmap = px.imshow(
    country_sector_pd,
    labels=dict(x="Sector", y="Country", color="Exposure (£)"),
    title="Country vs Sector Exposure Heatmap",
    color_continuous_scale='RdYlBu_r',
    aspect='auto'
)
fig_heatmap.update_layout(height=600)
st.plotly_chart(fig_heatmap, width=1200)

# ==================== CONCENTRATION METRICS ====================

st.subheader("Geographic Concentration Risks")

col1, col2, col3 = st.columns(3)

with col1:
    # Top country concentration
    top_3_exposure = country_stats.head(3).select(pl.col('total_exposure').sum()).item()
    top_3_pct = (top_3_exposure / total_exposure) * 100
    
    st.metric(
        "Top 3 Countries",
        f"{top_3_pct:.1f}%",
        delta="of total exposure",
        delta_color="inverse" if top_3_pct > 60 else "normal"
    )

with col2:
    # Single country limit
    max_country_pct = country_stats.select(pl.col('portfolio_pct').max()).item()
    
    st.metric(
        "Largest Country",
        f"{max_country_pct:.1f}%",
        delta="Single country exposure",
        delta_color="inverse" if max_country_pct > 30 else "normal"
    )

with col3:
    # Countries > 10%
    large_countries = len(country_stats.filter(pl.col('portfolio_pct') > 10))
    
    st.metric(
        "Countries > 10%",
        large_countries,
        help="Number of countries with >10% portfolio exposure"
    )

# ==================== DETAILED COUNTRY ANALYSIS ====================

st.subheader("Country Deep Dive")

# Country selector
selected_country = st.selectbox(
    "Select Country for Detailed Analysis",
    options=sorted(df['country'].unique().to_list())
)

if selected_country:
    country_df = df.filter(pl.col('country') == selected_country)
    
    # Country metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Loans",
            len(country_df)
        )
    
    with col2:
        country_exp = country_df.select(pl.col('amount').sum()).item()
        st.metric(
            "Total Exposure",
            f"£{country_exp/1e6:.1f}M"
        )
    
    with col3:
        country_rate = country_df.select(pl.col('rate').mean()).item()
        st.metric(
            "Avg Interest Rate",
            f"{country_rate:.2f}%"
        )
    
    with col4:
        country_borrowers = country_df.select(pl.col('borrower').n_unique())
        st.metric(
            "Unique Borrowers",
            country_borrowers
        )
    
    # Country breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        # Sector breakdown
        country_sectors = country_df.group_by('sector').agg([
            pl.col('amount').sum().alias('exposure')
        ]).sort('exposure', descending=True)
        
        fig_sector = px.pie(
            country_sectors.to_dicts(),
            values='exposure',
            names='sector',
            title=f'{selected_country} - Sector Distribution',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_sector.update_layout(height=350)
        st.plotly_chart(fig_sector, width=500)
    
    with col2:
        # Rating breakdown
        country_ratings = country_df.group_by('credit_rating').agg([
            pl.col('loan_id').count().alias('count')
        ]).sort('credit_rating')
        
        fig_rating = px.bar(
            country_ratings.to_dicts(),
            x='credit_rating',
            y='count',
            title=f'{selected_country} - Credit Rating Distribution',
            labels={'credit_rating': 'Rating', 'count': 'Number of Loans'},
            color='count',
            color_continuous_scale='RdYlGn_r'
        )
        fig_rating.update_layout(height=350)
        st.plotly_chart(fig_rating, width=500)
    
    # Country loan details
    st.write(f"**Loan Details - {selected_country}**")
    
    country_detail = country_df.select([
        'loan_id',
        'borrower',
        'amount',
        'rate',
        'sector',
        'credit_rating',
        'maturity_date',
        'status'
    ]).sort('amount', descending=True)
    
    # Format for display
    display_df = country_detail.to_pandas()
    display_df['amount'] = display_df['amount'].apply(lambda x: f"£{x/1e6:.2f}M")
    display_df['rate'] = display_df['rate'].apply(lambda x: f"{x:.2f}%")
    
    display_df.columns = ['Loan ID', 'Borrower', 'Amount', 'Rate', 'Sector', 'Rating', 'Maturity', 'Status']
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=350
    )

# ==================== EXPORT ====================

st.subheader("Export Geographic Analysis")

col1, col2 = st.columns(2)

with col1:
    # Export country summary
    csv_data = country_stats.write_csv()
    st.download_button(
        label="📥 Download Country Summary (CSV)",
        data=csv_data,
        file_name=f"geographic_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    st.write("**Analysis Summary:**")
    st.write(f"- Total Countries: {total_countries}")
    st.write(f"- Geographic HHI: {hhi:.0f} ({hhi_status})")
    st.write(f"- Top Country: {top_country['country']} ({top_country['portfolio_pct']:.1f}%)")
    st.write(f"- Top 3 Concentration: {top_3_pct:.1f}%")

st.info("💡 **Note:** Geographic diversification reduces country-specific risks. HHI < 1500 indicates low concentration, 1500-2500 moderate, >2500 high concentration.")
