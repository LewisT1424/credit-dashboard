import streamlit as st 
import polars as pl 
import plotly.express as px  
import plotly.graph_objects as go
import logging
from utils import (calculate_summary_stats, get_top_exposures, apply_filters, 
                   export_to_excel, get_risk_level)

# Configure logging for security and debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Credit Dashboard - Overview",
    layout="wide"
)

# Initialize session state variables
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = None
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
st.markdown("### Portfolio Overview & Summary")

with st.sidebar:
    st.subheader("Portfolio Data") 
    
    # Automatically load sample data by default
    use_sample = st.checkbox("Use sample portfolio data", value=True)
    uploaded_file = st.file_uploader("Or upload your own CSV file", type=['csv'])
    
    try:
        if use_sample and uploaded_file is None:
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
                st.session_state.portfolio_data = df
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


if st.session_state.portfolio_data is not None:
    df = st.session_state.portfolio_data
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
    
    # Apply filters with session state
    sector_filter = st.sidebar.multiselect(
        "Sector", 
        sectors, 
        default=st.session_state.sector_filter,
        key='sector_select'
    )
    rating_filter = st.sidebar.multiselect(
        "Credit Rating", 
        ratings, 
        default=st.session_state.rating_filter,
        key='rating_select'
    )
    status_filter = st.sidebar.multiselect(
        "Status", 
        statuses, 
        default=st.session_state.status_filter,
        key='status_select'
    )
    
    # Loan size range filter
    min_loan = df['amount'].min() / 1e6
    max_loan = df['amount'].max() / 1e6
    loan_size_range = st.sidebar.slider(
        "Loan Size Range (£M)",
        float(min_loan),
        float(max_loan),
        st.session_state.loan_size_range,
        key='loan_size_select'
    )
    
    # Update session state with current selections
    st.session_state.sector_filter = sector_filter
    st.session_state.rating_filter = rating_filter
    st.session_state.status_filter = status_filter
    st.session_state.loan_size_range = loan_size_range
    
    # Apply all filters
    filtered_df = apply_filters(df, sector_filter, rating_filter, status_filter, loan_size_range)
    
    # Store filtered df in session state
    st.session_state.filtered_df = filtered_df
    
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
        
        st.dataframe(display_exposures, width="stretch", hide_index=True)
    
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
                title="By Value (%)",
                height=450
            )
            fig_rating.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_rating, width="stretch")
            
            # Quality mix table
            st.dataframe(
                summary['quality_mix'].select([
                    pl.col('credit_rating').alias('Rating'),
                    pl.col('count').alias('# Loans'),
                    pl.col('value_mm').round(2).alias('Value (£M)'),
                    pl.col('pct_value').round(1).alias('% Value')
                ]),
                width="stretch",
                hide_index=True
            )
        except Exception as e:
            logger.error(f"Error creating rating chart: {str(e)}")
            st.error("Could not generate credit rating distribution chart")
    
    with chart_col2:
        st.markdown("**Distribution by Sector**")
        
        try:
            from utils import calculate_risk_metrics
            risk_metrics = calculate_risk_metrics(filtered_df)
            if risk_metrics:
                sector_data = risk_metrics['sector_concentration']
                
                fig_sector = px.pie(
                    sector_data, 
                    values='pct_value', 
                    names='sector',
                    title="By Value (%)",
                    height=450
                )
                fig_sector.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_sector, width="stretch")
                
                # Sector concentration table
                st.dataframe(
                    sector_data.select([
                        pl.col('sector').alias('Sector'),
                        pl.col('count').alias('# Loans'),
                        pl.col('value_mm').round(2).alias('Value (£M)'),
                        pl.col('pct_value').round(1).alias('% Value')
                    ]),
                    width="stretch",
                    hide_index=True
                )
        except Exception as e:
            logger.error(f"Error creating sector chart: {str(e)}")
            st.error("Could not generate sector distribution chart")
    
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
    
    st.dataframe(display_df, width="stretch", hide_index=True)

else:
    st.info("Please upload a portfolio CSV file or select 'Use sample portfolio data' from the sidebar to get started.")
