import streamlit as st 
import polars as pl 
import plotly.express as px  
import plotly.graph_objects as go
from io import BytesIO
import logging

# Configure logging for security and debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
        page_title="Credit Dashboard",
        layout="wide"
        )

# Initialize session state variables
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "df" not in st.session_state:
    st.session_state.df = None
if "watch_list_amount" not in st.session_state:
    st.session_state.watch_list_amount = 0
if "watch_list_count" not in st.session_state:
    st.session_state.watch_list_count = 0
if "watch_list_pct" not in st.session_state:
    st.session_state.watch_list_pct = 0
if "defaulted_amount" not in st.session_state:
    st.session_state.defaulted_amount = 0
if "defaulted_count" not in st.session_state:
    st.session_state.defaulted_count = 0
if "defaulted_pct" not in st.session_state:
    st.session_state.defaulted_pct = 0

uploaded = False

st.title("Credit Fund Portfolio Dashboard")

with st.sidebar:
    st.subheader("Configuration")
    
    # Theme toggle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Light Mode", use_container_width=True):
            st.session_state.theme = "light"
    with col2:
        if st.button("Dark Mode", use_container_width=True):
            st.session_state.theme = "dark"
    
    st.divider()
    st.subheader("Upload Portfolio Data") 
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    # Option to use sample data
    use_sample = st.checkbox("Use sample portfolio data", value=False)
    
    try:
        if use_sample:
            df = pl.read_csv('data/sample_portfolio.csv')
            uploaded = True
        elif uploaded_file is not None:
            # Security: Validate file size (max 50MB)
            if uploaded_file.size > 50 * 1024 * 1024:
                st.error("File size exceeds 50MB limit")
                uploaded = False
            else:
                df = pl.read_csv(uploaded_file)
                uploaded = True
        
        if uploaded:
            # Validate required columns
            required_cols = {'amount', 'rate', 'status', 'credit_rating', 'sector'}
            if not required_cols.issubset(set(df.columns)):
                st.error(f"Missing required columns: {required_cols - set(df.columns)}")
                uploaded = False
            else:
                # Calculate key risk metrics
                watch_list_amount = df.filter(pl.col('status') == 'Watch List')['amount'].sum()
                watch_list_count = df.filter(pl.col('status') == 'Watch List').height
                watch_list_pct = (watch_list_amount / df['amount'].sum()) * 100
                
                defaulted_amount = df.filter(pl.col('status') == 'Defaulted')['amount'].sum()
                defaulted_count = df.filter(pl.col('status') == 'Defaulted').height
                defaulted_pct = (defaulted_amount / df['amount'].sum()) * 100
                
                # Store in session state
                st.session_state.df = df
                st.session_state.watch_list_amount = watch_list_amount
                st.session_state.watch_list_count = watch_list_count
                st.session_state.watch_list_pct = watch_list_pct
                st.session_state.defaulted_amount = defaulted_amount
                st.session_state.defaulted_count = defaulted_count
                st.session_state.defaulted_pct = defaulted_pct

    except pl.exceptions.ComputeError as e:
        logger.error(f"Data processing error: {str(e)}")
        st.error("Error processing CSV file. Please check the format and try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")



def calculate_summary_stats(df):
    """Calculate portfolio summary statistics"""
    try:
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
    except Exception as e:
        logger.error(f"Error calculating summary stats: {str(e)}")
        return None


def get_top_exposures(df, n=5):
    """Get top N largest loans"""
    try:
        base_cols = ['loan_id', 'borrower', 'amount', 'rate', 'sector', 'credit_rating', 'status']
        available_cols = [col for col in base_cols if col in df.columns]
        
        return df.select(available_cols).sort('amount', descending=True).head(n).with_columns(
            (pl.col('amount') / 1e6).alias('amount_mm'),
            ((pl.col('amount') / df['amount'].sum()) * 100).alias('pct_portfolio')
        )
    except Exception as e:
        logger.error(f"Error getting top exposures: {str(e)}")
        return None


def apply_filters(df, sector_filter, rating_filter, status_filter, loan_size_range):
    """Apply multiple filters to dataframe"""
    try:
        filtered_df = df.clone()
        
        if sector_filter:
            filtered_df = filtered_df.filter(pl.col('sector').is_in(sector_filter))
        
        if rating_filter:
            filtered_df = filtered_df.filter(pl.col('credit_rating').is_in(rating_filter))
        
        if status_filter:
            filtered_df = filtered_df.filter(pl.col('status').is_in(status_filter))
        
        if loan_size_range:
            min_size, max_size = loan_size_range
            filtered_df = filtered_df.filter(
                (pl.col('amount') >= min_size * 1e6) & 
                (pl.col('amount') <= max_size * 1e6)
            )
        
        return filtered_df
    except Exception as e:
        logger.error(f"Error applying filters: {str(e)}")
        return df


def export_to_excel(df):
    """Export dataframe to Excel format"""
    try:
        output = BytesIO()
        df.write_excel(output)
        output.seek(0)
        return output
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return None


def get_risk_level(value, thresholds):
    """Determine risk level based on thresholds (Low, Medium, High)"""
    if value <= thresholds['low']:
        return "Low Risk"
    elif value <= thresholds['medium']:
        return "Medium Risk"
    else:
        return "High Risk"


def calculate_risk_metrics(df):
    """Calculate portfolio risk metrics"""
    try:
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
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {str(e)}")
        return None


if st.session_state.df is not None:
    df = st.session_state.df
    uploaded = True
    
    # Risk warnings at the top
    col_warn1, col_warn2 = st.columns(2)
    
    with col_warn1:
        if st.session_state.watch_list_count > 0:
            st.warning(f"Alert: Watch List - {st.session_state.watch_list_count} loans (£{st.session_state.watch_list_amount/1e6:.1f}M, {st.session_state.watch_list_pct:.1f}% of portfolio)")
    
    with col_warn2:
        if st.session_state.defaulted_count > 0:
            st.error(f"Alert: Defaulted - {st.session_state.defaulted_count} loans (£{st.session_state.defaulted_amount/1e6:.1f}M, {st.session_state.defaulted_pct:.1f}% of portfolio)")
    
    st.divider()
    
    # Sidebar filters
    st.sidebar.divider()
    st.sidebar.subheader("Filters")
    
    # Get unique values for filters
    sectors = sorted(df['sector'].unique().to_list())
    ratings = sorted(df['credit_rating'].unique().to_list())
    statuses = sorted(df['status'].unique().to_list())
    
    # Apply filters
    sector_filter = st.sidebar.multiselect("Sector", sectors, default=sectors)
    rating_filter = st.sidebar.multiselect("Credit Rating", ratings, default=ratings)
    status_filter = st.sidebar.multiselect("Status", statuses, default=statuses)
    
    # Loan size range filter
    min_loan = df['amount'].min() / 1e6
    max_loan = df['amount'].max() / 1e6
    loan_size_range = st.sidebar.slider(
        "Loan Size Range (£M)",
        float(min_loan),
        float(max_loan),
        (float(min_loan), float(max_loan))
    )
    
    # Apply all filters
    filtered_df = apply_filters(df, sector_filter, rating_filter, status_filter, loan_size_range)
    
    # Export button
    excel_file = export_to_excel(filtered_df)
    if excel_file:
        st.sidebar.download_button(
            label="Download Filtered Data (Excel)",
            data=excel_file,
            file_name="portfolio_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.subheader("Portfolio Summary")
    st.info(f"Showing {len(filtered_df)} of {len(df)} loans")
    
    summary = calculate_summary_stats(filtered_df)
    
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Value",
                f"£{summary['total_value']:.2f}M",
                delta=f"{(len(filtered_df)/len(df)*100):.0f}% of total"
            )
        
        with col2:
            st.metric(
                "Number of Loans",
                summary['num_of_loans']
            )
        
        with col3:
            st.metric(
                "Average Loan Size",
                f"£{summary['avg_loan_size']:.2f}M"
            )
        
        with col4:
            yield_risk = get_risk_level(
                summary['avg_yield'],
                {'low': 3, 'medium': 5}
            )
            st.metric(
                "Weighted Average Yield",
                f"{summary['avg_yield']:.2f}%",
                delta=yield_risk
            )
    
    st.divider()
    
    # Top 5 Exposures
    st.subheader("Top 5 Largest Exposures")
    
    top_exposures = get_top_exposures(filtered_df, 5)
    
    if top_exposures is not None:
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
    st.subheader("Portfolio Composition")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Distribution by Credit Rating**")
        
        try:
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
        except Exception as e:
            logger.error(f"Error creating rating chart: {str(e)}")
            st.error("Could not generate credit rating distribution chart")
    
    with chart_col2:
        st.markdown("**Distribution by Sector**")
        
        try:
            risk_metrics = calculate_risk_metrics(filtered_df)
            if risk_metrics:
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
        except Exception as e:
            logger.error(f"Error creating sector chart: {str(e)}")
            st.error("Could not generate sector distribution chart")
    
    st.divider()
    
    # Risk Analysis
    st.subheader("Risk Analysis")
    
    risk_col1, risk_col2 = st.columns(2)
    
    with risk_col1:
        st.markdown("**Portfolio Status Breakdown**")
        
        try:
            risk_metrics = calculate_risk_metrics(filtered_df)
            if risk_metrics:
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
        except Exception as e:
            logger.error(f"Error creating status chart: {str(e)}")
            st.error("Could not generate status breakdown chart")
    
    with risk_col2:
        st.markdown("**Sector Concentration Risk**")
        
        try:
            risk_metrics = calculate_risk_metrics(filtered_df)
            if risk_metrics:
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
        except Exception as e:
            logger.error(f"Error creating sector bar chart: {str(e)}")
            st.error("Could not generate sector concentration chart")
    
    st.divider()
    
    # Full Portfolio Data
    st.subheader("Full Portfolio Data")
    
    # Format the dataframe for display
    base_cols = ['loan_id', 'borrower', 'amount', 'rate', 'sector', 'maturity_date', 'credit_rating', 'status']
    display_cols = [col for col in base_cols if col in filtered_df.columns]
    
    display_df = filtered_df.with_columns([
        (pl.col('amount') / 1e6).round(2).alias('amount_mm')
    ]).select(display_cols)
    
    # Rename columns for display
    col_map = {
        'loan_id': 'Loan ID',
        'borrower': 'Borrower',
        'amount_mm': 'Amount (£M)',
        'rate': 'Rate (%)',
        'sector': 'Sector',
        'maturity_date': 'Maturity',
        'credit_rating': 'Rating',
        'status': 'Status'
    }
    
    for old, new in col_map.items():
        if old in display_df.columns:
            display_df = display_df.rename({old: new})
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("Please upload a portfolio CSV file or select 'Use sample portfolio data' from the sidebar to get started.")

        
