import streamlit as st 
import polars as pl 
import plotly.express as px  
import plotly.graph_objects as go


st.set_page_config(
        page_title="Credit Dashboard",
        layout="wide"
        )

uploaded = False

st.title("🏦 Credit Fund Portfolio Dashboard")

with st.sidebar:
    st.subheader("📁 Upload Portfolio Data") 
    uploaded_file = st.file_uploader("Choose a CSV file", type='csv')
    
    # Option to use sample data
    use_sample = st.checkbox("Use sample portfolio data", value=False)
    
    try:
        if use_sample:
            df = pl.read_csv('data/sample_portfolio.csv')
            uploaded = True
        elif uploaded_file is not None:
            df = pl.read_csv(uploaded_file)
            uploaded = True
        
        if uploaded:
            # Calculate key risk metrics
            watch_list_amount = df.filter(pl.col('status') == 'Watch List')['amount'].sum()
            watch_list_count = df.filter(pl.col('status') == 'Watch List').height
            watch_list_pct = (watch_list_amount / df['amount'].sum()) * 100
            
            defaulted_amount = df.filter(pl.col('status') == 'Defaulted')['amount'].sum()
            defaulted_count = df.filter(pl.col('status') == 'Defaulted').height
            defaulted_pct = (defaulted_amount / df['amount'].sum()) * 100

    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        uploaded = False



def calculate_summary_stats(df):
    """Calculate portfolio summary statistics"""
    total_val = df['amount'].sum() / 1e6
    total_num = len(df)
    avg_loan_size = total_val / total_num
    
    # Weighted average yield
    total_amount = df['amount'].sum()
    weighted_yield = (df['amount'] * df['rate']).sum() / total_amount
    
    quality_mix = df.group_by('credit_rating').agg([
        pl.len().alias("count"),
        pl.col('amount').sum().alias("total_amount")
    ]).with_columns([
        ((pl.col('count') / df.height) * 100).alias("pct_loans"),
        ((pl.col('total_amount') / df['amount'].sum()) * 100).alias("pct_value"),
        (pl.col('total_amount') / 1e6).alias("value_mm")
    ]).sort("pct_value", descending=True)

    results = {
        'total_value': total_val,
        'num_of_loans': total_num,
        'avg_yield': weighted_yield,
        'avg_loan_size': avg_loan_size,
        'quality_mix': quality_mix
    }

    return results


def get_top_exposures(df, n=5):
    """Get top N largest loans"""
    return df.select([
        'loan_id', 'borrower', 'amount', 'rate', 'sector', 
        'credit_rating', 'status'
    ]).sort('amount', descending=True).head(n).with_columns(
        (pl.col('amount') / 1e6).alias('amount_mm'),
        ((pl.col('amount') / df['amount'].sum()) * 100).alias('pct_portfolio')
    )


def calculate_risk_metrics(df):
    """Calculate portfolio risk metrics"""
    total_amount = df['amount'].sum()
    
    # Status breakdown
    status_breakdown = df.group_by('status').agg([
        pl.len().alias('count'),
        pl.col('amount').sum().alias('total_amount')
    ]).with_columns([
        ((pl.col('total_amount') / total_amount) * 100).alias('pct_value'),
        (pl.col('total_amount') / 1e6).alias('value_mm')
    ])
    
    # Sector concentration
    sector_concentration = df.group_by('sector').agg([
        pl.len().alias('count'),
        pl.col('amount').sum().alias('total_amount')
    ]).with_columns([
        ((pl.col('total_amount') / total_amount) * 100).alias('pct_value'),
        (pl.col('total_amount') / 1e6).alias('value_mm')
    ]).sort('pct_value', descending=True)
    
    return {
        'status_breakdown': status_breakdown,
        'sector_concentration': sector_concentration
    }


if uploaded:
    
    # Risk warnings at the top
    col_warn1, col_warn2 = st.columns(2)
    
    with col_warn1:
        if watch_list_count > 0:
            st.warning(f"⚠️ **Watch List:** {watch_list_count} loans (£{watch_list_amount/1e6:.1f}M, {watch_list_pct:.1f}% of portfolio)")
    
    with col_warn2:
        if defaulted_count > 0:
            st.error(f"🚨 **Defaulted:** {defaulted_count} loans (£{defaulted_amount/1e6:.1f}M, {defaulted_pct:.1f}% of portfolio)")
    
    st.divider()
    
    # Portfolio Summary Metrics
    st.subheader("📊 Portfolio Summary")
    
    summary = calculate_summary_stats(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"£{summary['total_value']:.1f}M")
    
    with col2:
        st.metric("Number of Loans", summary['num_of_loans'])
    
    with col3:
        st.metric("Average Loan Size", f"£{summary['avg_loan_size']:.1f}M")
    
    with col4:
        st.metric("Weighted Avg Yield", f"{summary['avg_yield']:.2f}%")
    
    st.divider()
    
    # Top 5 Exposures
    st.subheader("🎯 Top 5 Largest Exposures")
    
    top_exposures = get_top_exposures(df, 5)
    
    # Display as formatted table
    display_exposures = top_exposures.select([
        pl.col('loan_id').alias('Loan ID'),
        pl.col('borrower').alias('Borrower'),
        pl.col('amount_mm').round(2).alias('Amount (£M)'),
        pl.col('pct_portfolio').round(1).alias('% of Portfolio'),
        pl.col('rate').alias('Rate (%)'),
        pl.col('sector').alias('Sector'),
        pl.col('credit_rating').alias('Rating'),
        pl.col('status').alias('Status')
    ])
    
    st.dataframe(display_exposures, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Portfolio Composition Charts
    st.subheader("📈 Portfolio Composition")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Distribution by Credit Rating**")
        
        # Pie chart for credit ratings
        quality_chart_data = summary['quality_mix'].select([
            'credit_rating',
            'pct_value'
        ])
        
        fig_rating = px.pie(
            quality_chart_data, 
            values='pct_value', 
            names='credit_rating',
            title="By Value (%)"
        )
        fig_rating.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_rating, use_container_width=True)
        
        # Quality mix table
        st.dataframe(
            summary['quality_mix'].select([
                pl.col('credit_rating').alias('Rating'),
                pl.col('count').alias('# Loans'),
                pl.col('value_mm').round(2).alias('Value (£M)'),
                pl.col('pct_value').round(1).alias('% Value')
            ]),
            use_container_width=True,
            hide_index=True
        )
    
    with chart_col2:
        st.markdown("**Distribution by Sector**")
        
        risk_metrics = calculate_risk_metrics(df)
        sector_data = risk_metrics['sector_concentration']
        
        fig_sector = px.pie(
            sector_data, 
            values='pct_value', 
            names='sector',
            title="By Value (%)"
        )
        fig_sector.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_sector, use_container_width=True)
        
        # Sector concentration table
        st.dataframe(
            sector_data.select([
                pl.col('sector').alias('Sector'),
                pl.col('count').alias('# Loans'),
                pl.col('value_mm').round(2).alias('Value (£M)'),
                pl.col('pct_value').round(1).alias('% Value')
            ]),
            use_container_width=True,
            hide_index=True
        )
    
    st.divider()
    
    # Risk Analysis
    st.subheader("⚠️ Risk Analysis")
    
    risk_col1, risk_col2 = st.columns(2)
    
    with risk_col1:
        st.markdown("**Portfolio Status Breakdown**")
        
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
            showlegend=False
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with risk_col2:
        st.markdown("**Sector Concentration Risk**")
        
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
            showlegend=False
        )
        st.plotly_chart(fig_sector_bar, use_container_width=True)
    
    st.divider()
    
    # Full Portfolio Data
    st.subheader("📋 Full Portfolio Data")
    
    # Format the dataframe for display
    display_df = df.with_columns([
        (pl.col('amount') / 1e6).round(2).alias('amount_mm')
    ]).select([
        pl.col('loan_id').alias('Loan ID'),
        pl.col('borrower').alias('Borrower'),
        pl.col('amount_mm').alias('Amount (£M)'),
        pl.col('rate').alias('Rate (%)'),
        pl.col('sector').alias('Sector'),
        pl.col('maturity_date').alias('Maturity'),
        pl.col('credit_rating').alias('Rating'),
        pl.col('status').alias('Status')
    ])
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("👆 Please upload a portfolio CSV file or select 'Use sample portfolio data' from the sidebar to get started.")
    
    with st.expander("📖 Expected CSV Format"):
        st.markdown("""
        Your CSV file should contain the following columns:
        
        - `loan_id`: Unique identifier for each loan
        - `borrower`: Name of the borrowing entity
        - `amount`: Loan amount in £
        - `rate`: Interest rate (%)
        - `sector`: Industry sector
        - `maturity_date`: Loan maturity date (YYYY-MM-DD)
        - `credit_rating`: Credit rating (A, BBB, BB, B, CCC, etc.)
        - `status`: Loan status (Active, Watch List, Defaulted)
        """)

        
