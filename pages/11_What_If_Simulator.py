import streamlit as st
import polars as pl
import plotly.graph_objects as go
import plotly.express as px
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

st.set_page_config(page_title="What-If Simulator", layout="wide")

st.title("What-If Simulator")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# ==================== SCENARIO SELECTION ====================

st.subheader("Portfolio Scenario Analysis")

st.write("Adjust portfolio parameters below to simulate different scenarios and analyze impacts on portfolio metrics.")

# Create tabs for different simulation types
tab1, tab2, tab3, tab4 = st.tabs([
    "Interest Rate Changes",
    "Default Scenarios",
    "Borrower-Specific Changes",
    "Multi-Factor Scenario"
])

# ==================== TAB 1: INTEREST RATE CHANGES ====================

with tab1:
    st.write("Simulate the impact of interest rate changes on portfolio yield and valuation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ir_change = st.slider(
            "Interest Rate Change (basis points)",
            min_value=-200,
            max_value=200,
            value=0,
            step=10,
            help="Positive = rates rise, Negative = rates fall"
        )
    
    with col2:
        st.metric("Rate Change", f"{ir_change:+.0f} bps")
    
    # Calculate impact
    baseline_yield = df.select(
        (pl.col('amount') * pl.col('rate') / 100).sum() / pl.col('amount').sum()
    ).item()
    
    adjusted_yield = baseline_yield + (ir_change / 100)
    
    # Create adjusted dataframe
    df_ir_adj = df.with_columns([
        (pl.col('rate') + (ir_change / 100)).alias('adjusted_rate')
    ])
    
    # Calculate metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Baseline Portfolio Yield", f"{baseline_yield:.2f}%")
    
    with col2:
        st.metric("Adjusted Portfolio Yield", f"{adjusted_yield:.2f}%")
    
    with col3:
        current_revenue = df.select(
            (pl.col('amount') * pl.col('rate') / 100).sum()
        ).item()
        adjusted_revenue = df_ir_adj.select(
            (pl.col('amount') * pl.col('adjusted_rate') / 100).sum()
        ).item()
        revenue_impact = adjusted_revenue - current_revenue
        
        st.metric("Annual Revenue Impact", f"£{revenue_impact/1e6:.2f}M", delta=f"{revenue_impact/current_revenue*100:+.1f}%", delta_color="inverse")
    
    with col4:
        st.metric("Total Portfolio Value", f"£{df.select(pl.col('amount').sum()).item()/1e6:.1f}M")
    
    # Visualization by sector
    st.write("**Impact by Sector**")
    
    sector_impact = df_ir_adj.group_by('sector').agg([
        (pl.col('amount').sum()).alias('exposure'),
        (pl.col('rate').mean()).alias('baseline_rate'),
        (pl.col('adjusted_rate').mean()).alias('adjusted_rate')
    ]).with_columns([
        ((pl.col('adjusted_rate') - pl.col('baseline_rate')) * pl.col('exposure') / 100).alias('annual_impact')
    ])
    
    fig_sector_impact = px.bar(
        sector_impact.to_dicts(),
        x='sector',
        y='annual_impact',
        color='annual_impact',
        color_continuous_scale='RdYlGn',
        title='Annual Revenue Impact by Sector',
        labels={'annual_impact': 'Annual Impact (£)', 'sector': 'Sector'}
    )
    fig_sector_impact.update_layout(height=400)
    st.plotly_chart(fig_sector_impact, width=1200)
    
    # Top losers/winners
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top Losers** (if rates rise)")
        losers = df_ir_adj.with_columns([
            ((pl.col('rate') + (ir_change / 100) - pl.col('rate')) * pl.col('amount') / 100).alias('impact')
        ]).sort('amount', descending=True).head(5)
        
        for row in losers.to_dicts():
            st.write(f"• {row['loan_id']}: £{row['amount']/1e6:.2f}M @ {row['rate']:.2f}% → {row['rate'] + (ir_change/100):.2f}%")
    
    with col2:
        st.write("**Top Gainers** (if rates fall)")
        gainers = df_ir_adj.with_columns([
            ((pl.col('rate') + (ir_change / 100) - pl.col('rate')) * pl.col('amount') / 100).alias('impact')
        ]).sort('amount', descending=True).head(5)
        
        for row in gainers.to_dicts():
            st.write(f"• {row['loan_id']}: £{row['amount']/1e6:.2f}M @ {row['rate']:.2f}% → {row['rate'] + (ir_change/100):.2f}%")

# ==================== TAB 2: DEFAULT SCENARIOS ====================

with tab2:
    st.write("Simulate portfolio impact if specific credit ratings default at higher rates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        default_rating = st.selectbox(
            "Select Rating for Default Scenario",
            options=['B', 'B-', 'CCC+', 'CCC'],
            index=0
        )
    
    with col2:
        recovery_rate = st.slider(
            "Recovery Rate (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Expected recovery as % of principal"
        )
    
    with col3:
        additional_defaults = st.slider(
            "Additional Loans to Default (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            help="% of loans in selected rating to default"
        )
    
    # Calculate default impact
    vulnerable = df.filter(pl.col('credit_rating') == default_rating)
    
    if len(vulnerable) == 0:
        st.warning(f"No loans with rating {default_rating} found in portfolio")
    else:
        default_count = max(1, int(len(vulnerable) * (additional_defaults / 100)))
        default_loans = vulnerable.sort('amount', descending=True).head(default_count)
        default_amount = default_loans.select(pl.col('amount').sum()).item()
        loss_amount = default_amount * (1 - recovery_rate / 100)
        
        # Calculate adjusted portfolio after defaults
        defaulted_loan_ids = default_loans['loan_id'].to_list()
        df_default = df.filter(~pl.col('loan_id').is_in(defaulted_loan_ids))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Rating Selected", default_rating)
        
        with col2:
            st.metric("Loans Defaulting", default_count)
        
        with col3:
            st.metric("Default Amount", f"£{default_amount/1e6:.2f}M")
        
        with col4:
            total_exposure = df.select(pl.col('amount').sum()).item()
            loss_pct = (loss_amount / total_exposure) * 100
            st.metric("Loss (after recovery)", f"£{loss_amount/1e6:.2f}M", delta=f"{loss_pct:.2f}% of portfolio", delta_color="off")
        
        # Impact visualization
        fig_default = go.Figure()
        
        current_total = df.select(pl.col('amount').sum()).item()
        remaining_total = df_default.select(pl.col('amount').sum()).item()
        
        fig_default.add_trace(go.Bar(
            x=['Current Portfolio', 'After Default'],
            y=[current_total, remaining_total],
            name='Portfolio Value',
            marker_color='lightblue'
        ))
        
        fig_default.add_trace(go.Bar(
            x=['Current Portfolio', 'After Default'],
            y=[0, loss_amount],
            name='Actual Loss',
            marker_color='red'
        ))
        
        fig_default.update_layout(
            title='Portfolio Impact - Default Scenario',
            yaxis_title='Amount (£)',
            barmode='stack',
            height=450
        )
        st.plotly_chart(fig_default, width=1200)
        
        # Risk distribution
        st.write("**Risk Concentration by Rating**")
        
        rating_exposure = df.group_by('credit_rating').agg(
            pl.col('amount').sum().alias('exposure'),
            pl.col('loan_id').count().alias('count')
        ).with_columns([
            (pl.col('exposure') / total_exposure * 100).alias('pct_portfolio')
        ]).sort('exposure', descending=True)
        
        fig_rating_exp = px.pie(
            rating_exposure.to_dicts(),
            values='exposure',
            names='credit_rating',
            title='Portfolio Exposure by Credit Rating'
        )
        fig_rating_exp.update_layout(height=450)
        st.plotly_chart(fig_rating_exp, width=900)

# ==================== TAB 3: BORROWER-SPECIFIC CHANGES ====================

with tab3:
    st.write("Simulate impact of changes to a specific borrower's loans")
    
    borrowers = sorted(df.select('borrower').unique()['borrower'].to_list())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_borrower = st.selectbox(
            "Select Borrower",
            borrowers,
            key="borrower_simulator"
        )
    
    borrower_loans = df.filter(pl.col('borrower') == selected_borrower)
    
    with col2:
        rate_change = st.slider(
            "Interest Rate Change (%)",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.5
        )
    
    with col3:
        default_option = st.checkbox("Default All Loans", value=False)
    
    # Display borrower info
    st.write(f"**{selected_borrower}**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Loans", len(borrower_loans))
    
    with col2:
        total_exp = borrower_loans.select(pl.col('amount').sum()).item()
        st.metric("Total Exposure", f"£{total_exp/1e6:.2f}M")
    
    with col3:
        pct_portfolio = (total_exp / df.select(pl.col('amount').sum()).item()) * 100
        st.metric("% of Portfolio", f"{pct_portfolio:.2f}%")
    
    with col4:
        st.metric("Avg Rating", borrower_loans.select('credit_rating').n_unique())
    
    # Create adjusted borrower data
    total_portfolio = df.select(pl.col('amount').sum()).item()
    
    if default_option:
        loss_amount = total_exp
        df_borrower_adj = df.filter(~(pl.col('borrower') == selected_borrower))
        original_revenue = borrower_loans.select(
            (pl.col('amount') * pl.col('rate') / 100).sum()
        ).item()
        
        st.error(f"⚠️ Defaulting {len(borrower_loans)} loans would result in £{loss_amount/1e6:.2f}M loss ({loss_amount/total_portfolio*100:.2f}% of portfolio)")
        
        revenue_impact = -original_revenue
    else:
        # Create adjusted dataframe with modified rates for selected borrower
        df_borrower_adj = df.with_columns([
            pl.when(pl.col('borrower') == selected_borrower)
            .then(pl.col('rate') + rate_change)
            .otherwise(pl.col('rate'))
            .alias('adjusted_rate')
        ])
        
        original_revenue = borrower_loans.select(
            (pl.col('amount') * pl.col('rate') / 100).sum()
        ).item()
        
        adjusted_revenue = borrower_loans.with_columns([
            (pl.col('rate') + rate_change).alias('adjusted_rate')
        ]).select(
            (pl.col('amount') * pl.col('adjusted_rate') / 100).sum()
        ).item()
        
        revenue_impact = adjusted_revenue - original_revenue
        
        delta_text = f"+£{revenue_impact/1e6:.3f}M" if revenue_impact > 0 else f"£{revenue_impact/1e6:.3f}M"
        st.info(f"Revenue impact for {selected_borrower}: {delta_text}")
    
    # Impact on portfolio metrics
    st.write("**Portfolio Impact**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        baseline_total = df.select(pl.col('amount').sum()).item()
        if default_option:
            adjusted_total = df_borrower_adj.select(pl.col('amount').sum()).item()
            delta_exp = adjusted_total - baseline_total
            st.metric("Portfolio Exposure", f"£{adjusted_total/1e6:.1f}M", delta=f"£{delta_exp/1e6:.2f}M", delta_color="inverse")
        else:
            st.metric("Portfolio Exposure", f"£{baseline_total/1e6:.1f}M", delta="No change")
    
    with col2:
        baseline_yield = df.select(
            (pl.col('amount') * pl.col('rate') / 100).sum() / pl.col('amount').sum()
        ).item()
        
        if default_option:
            adjusted_yield = df_borrower_adj.select(
                (pl.col('amount') * pl.col('rate') / 100).sum() / pl.col('amount').sum()
            ).item()
        else:
            adjusted_yield = df_borrower_adj.select(
                (pl.col('amount') * pl.col('adjusted_rate') / 100).sum() / pl.col('amount').sum()
            ).item()
        
        yield_delta = adjusted_yield - baseline_yield
        delta_color = "normal" if yield_delta > 0 else "inverse" if yield_delta < 0 else "off"
        st.metric("Portfolio Yield", f"{adjusted_yield:.2f}%", delta=f"{yield_delta:+.2f}%", delta_color=delta_color)
    
    with col3:
        st.metric("Borrower Contribution", f"{pct_portfolio:.2f}%", help="This borrower's % of portfolio")
    
    with col4:
        if default_option:
            st.metric("Risk Impact", "HIGH", help="Default would significantly impact portfolio")
        else:
            st.metric("Rate Impact", f"{rate_change:+.1f}%")

# ==================== TAB 4: MULTI-FACTOR SCENARIO ====================

with tab4:
    st.write("Create a comprehensive scenario with multiple changes")
    
    st.subheader("Market Conditions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        macro_scenario = st.radio(
            "Macroeconomic Scenario",
            options=["Base Case", "Growth", "Recession"],
            index=0
        )
    
    with col2:
        ir_scenario = st.slider(
            "Interest Rate Scenario (bps)",
            min_value=-150,
            max_value=150,
            value=0,
            step=25
        )
    
    with col3:
        default_rate_increase = st.slider(
            "Default Rate Increase (%)",
            min_value=0,
            max_value=10,
            value=0,
            step=1
        )
    
    # Apply scenarios
    st.subheader("Scenario Results")
    
    # 1. Apply interest rate change
    df_scenario = df.with_columns([
        (pl.col('rate') + (ir_scenario / 100)).alias('scenario_rate')
    ])
    
    # 2. Calculate defaults based on rating and scenario
    if macro_scenario == "Recession":
        # In recession, more ratings at risk
        default_eligible = df_scenario.filter(pl.col('credit_rating').is_in(['B', 'B-', 'CCC+', 'CCC']))
    elif macro_scenario == "Growth":
        # In growth, only worst ratings
        default_eligible = df_scenario.filter(pl.col('credit_rating').is_in(['CCC']))
    else:  # Base Case
        default_eligible = df_scenario.filter(pl.col('credit_rating').is_in(['CCC']))  # Only worst case
    
    # Calculate defaults - handle empty case
    if len(default_eligible) > 0:
        defaulting_count = max(1, int(len(default_eligible) * (default_rate_increase / 100)))
    else:
        defaulting_count = 0
    
    # 3. Calculate metrics
    baseline_yield = df.select(
        (pl.col('amount') * pl.col('rate') / 100).sum() / pl.col('amount').sum()
    ).item()
    
    scenario_yield = df_scenario.select(
        (pl.col('amount') * pl.col('scenario_rate') / 100).sum() / pl.col('amount').sum()
    ).item()
    
    current_revenue = df.select(
        (pl.col('amount') * pl.col('rate') / 100).sum()
    ).item()
    
    scenario_revenue = df_scenario.select(
        (pl.col('amount') * pl.col('scenario_rate') / 100).sum()
    ).item()
    
    # Calculate expected loss from defaults
    if defaulting_count > 0 and len(default_eligible) > 0:
        expected_defaults = default_eligible.sort('amount', descending=True).head(defaulting_count)
        default_loss = expected_defaults.select(pl.col('amount').sum()).item() * 0.4  # Assume 40% loss rate
    else:
        default_loss = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        yield_delta = scenario_yield - baseline_yield
        delta_color = "inverse" if yield_delta < 0 else "normal" if yield_delta > 0 else "off"
        st.metric("Scenario Yield", f"{scenario_yield:.2f}%", delta=f"{yield_delta:+.2f}%", delta_color=delta_color)
    
    with col2:
        revenue_delta = scenario_revenue - current_revenue
        rev_color = "normal" if revenue_delta > 0 else "inverse" if revenue_delta < 0 else "off"
        st.metric("Annual Revenue", f"£{scenario_revenue/1e6:.2f}M", delta=f"£{revenue_delta/1e6:+.2f}M", delta_color=rev_color)
    
    with col3:
        st.metric("At-Risk Loans", defaulting_count, help=f"Loans expected to default in {macro_scenario}")
    
    with col4:
        if default_loss > 0:
            loss_pct = (default_loss / df.select(pl.col('amount').sum()).item()) * 100
            st.metric("Expected Loss", f"£{default_loss/1e6:.2f}M ({loss_pct:.2f}%)")
        else:
            st.metric("Expected Loss", "£0.00M")
    
    # Comparison visualization
    fig_scenario = go.Figure()
    
    fig_scenario.add_trace(go.Bar(
        x=['Current', f'{macro_scenario} Scenario'],
        y=[baseline_yield, scenario_yield],
        name='Portfolio Yield (%)',
        yaxis='y1',
        marker_color=['lightblue', 'orange']
    ))
    
    fig_scenario.add_trace(go.Bar(
        x=['Current', f'{macro_scenario} Scenario'],
        y=[current_revenue/1e6, scenario_revenue/1e6],
        name='Annual Revenue (£M)',
        yaxis='y2',
        marker_color=['lightgreen', 'lightcoral']
    ))
    
    fig_scenario.update_layout(
        title=f'{macro_scenario} Scenario Analysis',
        yaxis=dict(title='Portfolio Yield (%)'),
        yaxis2=dict(title='Annual Revenue (£M)', overlaying='y', side='right'),
        hovermode='x unified',
        height=450
    )
    
    st.plotly_chart(fig_scenario, width=1200)
    
    # Summary
    st.subheader("Key Insights")
    
    if macro_scenario == "Recession":
        if default_loss > 0:
            st.error(f"🔴 SEVERE: Recession scenario would trigger {defaulting_count} defaults with £{default_loss/1e6:.2f}M loss. Immediate risk mitigation required.")
        else:
            st.warning("🟠 In a recession scenario, lower-rated loans face increased default risk. Consider hedging strategies.")
    elif macro_scenario == "Growth":
        st.success(f"✓ Growth scenario supports portfolio expansion. Yield improves to {scenario_yield:.2f}% with minimal default risk.")
    else:
        st.info(f"Base case assumes stable economic conditions. Yield at {scenario_yield:.2f}% with interest rate changes of {ir_scenario:+.0f}bps.")
