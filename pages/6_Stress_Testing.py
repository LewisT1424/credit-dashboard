import streamlit as st
import polars as pl
from utils import calculate_stress_test
import plotly.graph_objects as go
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Stress Testing", layout="wide")

st.title("Stress Testing & Scenario Analysis")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

st.subheader("Scenario Builder")

# Define available scenarios
col1, col2 = st.columns(2)

with col1:
    st.write("**Interest Rate Shocks**")
    rate_shock_100 = st.checkbox("Rate +100 bps", value=True, key="rate_100")
    rate_shock_200 = st.checkbox("Rate +200 bps", key="rate_200")
    rate_shock_300 = st.checkbox("Rate +300 bps", key="rate_300")

with col2:
    st.write("**Default Rate Increases**")
    default_2pct = st.checkbox("Default +2%", value=True, key="default_2")
    default_5pct = st.checkbox("Default +5%", key="default_5")
    default_10pct = st.checkbox("Default +10%", key="default_10")

col1, col2 = st.columns(2)

with col1:
    st.write("**Recovery Rate Scenarios**")
    recovery_80 = st.checkbox("Recovery 80%", key="recovery_80")
    recovery_60 = st.checkbox("Recovery 60%", key="recovery_60")
    recovery_40 = st.checkbox("Recovery 40%", key="recovery_40")

with col2:
    st.write("**Special Scenarios**")
    combined = st.checkbox("Combined Stress", value=True, key="combined_stress")

# Build scenarios dictionary
scenarios = {
    'Base Case': {
        'rate_shock': 0,
        'default_increase': 0,
        'recovery_rate': 100
    }
}

if rate_shock_100:
    scenarios['Rate +100 bps'] = {'rate_shock': 100, 'default_increase': 0, 'recovery_rate': 100}
if rate_shock_200:
    scenarios['Rate +200 bps'] = {'rate_shock': 200, 'default_increase': 0, 'recovery_rate': 100}
if rate_shock_300:
    scenarios['Rate +300 bps'] = {'rate_shock': 300, 'default_increase': 0, 'recovery_rate': 100}

if default_2pct:
    scenarios['Default +2%'] = {'rate_shock': 0, 'default_increase': 2, 'recovery_rate': 100}
if default_5pct:
    scenarios['Default +5%'] = {'rate_shock': 0, 'default_increase': 5, 'recovery_rate': 100}
if default_10pct:
    scenarios['Default +10%'] = {'rate_shock': 0, 'default_increase': 10, 'recovery_rate': 100}

if recovery_80:
    scenarios['Recovery 80%'] = {'rate_shock': 0, 'default_increase': 2, 'recovery_rate': 80}
if recovery_60:
    scenarios['Recovery 60%'] = {'rate_shock': 0, 'default_increase': 5, 'recovery_rate': 60}
if recovery_40:
    scenarios['Recovery 40%'] = {'rate_shock': 0, 'default_increase': 10, 'recovery_rate': 40}

if combined:
    scenarios['Combined Stress'] = {'rate_shock': 200, 'default_increase': 5, 'recovery_rate': 80}

# Run stress tests
results = calculate_stress_test(df, scenarios)

if results is None:
    st.error("Unable to run stress tests")
    st.stop()

st.subheader("Stress Test Results")

# Display summary metrics
col1, col2, col3 = st.columns(3)

base_value = results.filter(pl.col('scenario') == 'Base Case')['base_value'][0]
worst_case = results['stressed_value'].min()
best_case = results['stressed_value'].max()

with col1:
    st.metric(
        "Base Case Portfolio Value",
        f"£{base_value:.2f}M"
    )

with col2:
    st.metric(
        "Worst Case Value",
        f"£{worst_case:.2f}M",
        delta=f"£{worst_case - base_value:.2f}M",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "Best Case Value",
        f"£{best_case:.2f}M",
        delta=f"£{best_case - base_value:.2f}M"
    )

# Results table
st.subheader("Scenario Comparison")

results_display = results.select([
    'scenario',
    'base_value',
    'stressed_value',
    'value_change',
    'pct_change',
    'base_yield',
    'stressed_yield',
    'estimated_defaults',
    'estimated_loss'
]).with_columns([
    pl.col('base_value').round(2),
    pl.col('stressed_value').round(2),
    pl.col('value_change').round(2),
    pl.col('pct_change').round(2),
    pl.col('base_yield').round(3),
    pl.col('stressed_yield').round(3),
    pl.col('estimated_loss').round(2)
])

st.dataframe(results_display, width=1200, height=600)

# Visualizations
st.subheader("Impact Analysis")

# Value change chart
fig_value = px.bar(
    results.to_pandas(),
    x='scenario',
    y='value_change',
    title='Portfolio Value Change by Scenario',
    labels={'value_change': 'Value Change (£M)', 'scenario': 'Scenario'},
    color='value_change',
    color_continuous_scale='RdYlGn'
)

fig_value.update_layout(height=400, template='plotly_white')
st.plotly_chart(fig_value, width=1200)

# Percentage change comparison
col1, col2 = st.columns(2)

with col1:
    fig_pct = px.bar(
        results.to_pandas(),
        x='scenario',
        y='pct_change',
        title='Portfolio Value % Change',
        labels={'pct_change': '% Change', 'scenario': 'Scenario'},
        color='pct_change',
        color_continuous_scale='RdYlGn'
    )
    fig_pct.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_pct, width=600)

with col2:
    # Estimated losses
    fig_loss = px.bar(
        results.to_pandas(),
        x='scenario',
        y='estimated_loss',
        title='Estimated Credit Losses',
        labels={'estimated_loss': 'Loss (£M)', 'scenario': 'Scenario'},
        color='estimated_loss',
        color_continuous_scale='Reds'
    )
    fig_loss.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_loss, width=600)

# Yield comparison
st.subheader("Yield Impact")

fig_yield = go.Figure()

fig_yield.add_trace(go.Bar(
    name='Base Yield',
    x=results['scenario'],
    y=results['base_yield'],
    marker_color='rgb(55, 83, 109)'
))

fig_yield.add_trace(go.Bar(
    name='Stressed Yield',
    x=results['scenario'],
    y=results['stressed_yield'],
    marker_color='rgb(210, 150, 56)'
))

fig_yield.update_layout(
    barmode='group',
    title='Portfolio Yield - Base vs Stressed',
    xaxis_title='Scenario',
    yaxis_title='Yield (%)',
    height=400,
    template='plotly_white'
)

st.plotly_chart(fig_yield, width=1200)

# Key insights
st.subheader("Stress Test Insights")

col1, col2, col3 = st.columns(3)

with col1:
    worst_scenario = results.filter(pl.col('value_change') == pl.col('value_change').min())['scenario'][0]
    worst_loss = results.filter(pl.col('value_change') == pl.col('value_change').min())['value_change'][0]
    st.warning(f"Worst scenario: {worst_scenario}\nValue impact: £{worst_loss:.2f}M")

with col2:
    total_losses = results.filter(pl.col('scenario') != 'Base Case')['estimated_loss'].sum()
    st.error(f"Total potential losses across scenarios: £{total_losses:.2f}M")

with col3:
    avg_rate_sensitivity = results.filter(pl.col('scenario').str.contains('Rate'))['pct_change'].mean() if len(results.filter(pl.col('scenario').str.contains('Rate'))) > 0 else 0
    st.info(f"Average rate shock sensitivity: {avg_rate_sensitivity:.2f}%")

# Download results
st.subheader("Export Results")

csv_data = results_display.write_csv()

st.download_button(
    label="Download Stress Test Results (CSV)",
    data=csv_data,
    file_name="stress_test_results.csv",
    mime="text/csv"
)
