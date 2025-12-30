import streamlit as st
import polars as pl
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import logging
import math

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Loan Amortization Details", layout="wide")

st.title("Loan Amortization Details")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# ==================== LOAN SELECTION ====================

st.subheader("Select Loan for Amortization Analysis")

# Get all loans
all_loans = df.select([
    'loan_id',
    'borrower',
    'amount',
    'rate'
]).to_dicts()

loan_options = [f"{loan['loan_id']} - {loan['borrower']} (£{loan['amount']/1e6:.2f}M @ {loan['rate']:.2f}%)" for loan in all_loans]
selected_loan_idx = st.selectbox("Select a loan", range(len(loan_options)), format_func=lambda x: loan_options[x])

if selected_loan_idx is not None:
    selected_loan = all_loans[selected_loan_idx]
    loan_id = selected_loan['loan_id']
    
    # Get full loan details
    loan_details = df.filter(pl.col('loan_id') == loan_id)
    
    if len(loan_details) > 0:
        loan = loan_details.to_dicts()[0]
        
        # ==================== LOAN INFORMATION ====================
        
        st.subheader(f"Loan Details: {loan_id}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Borrower", loan['borrower'])
        
        with col2:
            st.metric("Amount", f"£{loan['amount']/1e6:.2f}M")
        
        with col3:
            st.metric("Interest Rate", f"{loan['rate']:.2f}%")
        
        with col4:
            st.metric("Credit Rating", loan['credit_rating'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sector", loan['sector'])
        
        with col2:
            st.metric("Status", loan['status'])
        
        with col3:
            maturity = datetime.strptime(loan['maturity_date'], '%Y-%m-%d').date()
            st.metric("Maturity Date", maturity.strftime('%Y-%m-%d'))
        
        with col4:
            days_left = (maturity - datetime.now().date()).days
            st.metric("Days to Maturity", days_left)
        
        # ==================== AMORTIZATION PARAMETERS ====================
        
        st.subheader("Amortization Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Estimate loan term from maturity date
            origination_date = datetime.now().date() - timedelta(days=365)  # Assume 1 year already elapsed
            loan_term_years = max(1, (maturity - origination_date).days / 365.25)
            loan_term_years = st.number_input(
                "Estimated Loan Term (years)",
                min_value=0.5,
                max_value=30.0,
                value=round(loan_term_years, 1),
                step=0.5
            )
        
        with col2:
            amortization_type = st.selectbox(
                "Amortization Type",
                options=["Straight-line", "Annuity (Equal payments)", "Bullet (Balloon)"],
                index=1
            )
        
        with col3:
            payment_frequency = st.selectbox(
                "Payment Frequency",
                options=["Monthly", "Quarterly", "Semi-Annual", "Annual"],
                index=0
            )
        
        # ==================== CALCULATE AMORTIZATION SCHEDULE ====================
        
        def calculate_amortization_schedule(principal, annual_rate, term_years, frequency, amorization_type):
            """Calculate detailed amortization schedule"""
            
            # Determine number of periods
            if frequency == "Monthly":
                periods_per_year = 12
            elif frequency == "Quarterly":
                periods_per_year = 4
            elif frequency == "Semi-Annual":
                periods_per_year = 2
            else:  # Annual
                periods_per_year = 1
            
            total_periods = int(term_years * periods_per_year)
            period_rate = annual_rate / 100 / periods_per_year
            
            schedule = []
            remaining_balance = principal
            
            if amorization_type == "Straight-line":
                # Equal principal payments
                principal_payment = principal / total_periods
                
                for period in range(1, total_periods + 1):
                    interest_payment = remaining_balance * period_rate
                    total_payment = principal_payment + interest_payment
                    remaining_balance -= principal_payment
                    
                    schedule.append({
                        'period': period,
                        'payment': total_payment,
                        'principal': principal_payment,
                        'interest': interest_payment,
                        'balance': max(0, remaining_balance)
                    })
            
            elif amorization_type == "Annuity (Equal payments)":
                # Annuity formula for equal payments
                if period_rate == 0:
                    payment = principal / total_periods
                else:
                    payment = principal * (period_rate * (1 + period_rate)**total_periods) / \
                              ((1 + period_rate)**total_periods - 1)
                
                for period in range(1, total_periods + 1):
                    interest_payment = remaining_balance * period_rate
                    principal_payment = payment - interest_payment
                    remaining_balance -= principal_payment
                    
                    schedule.append({
                        'period': period,
                        'payment': payment,
                        'principal': principal_payment,
                        'interest': interest_payment,
                        'balance': max(0, remaining_balance)
                    })
            
            else:  # Bullet (Balloon)
                # Only interest during term, principal at end
                for period in range(1, total_periods + 1):
                    interest_payment = principal * period_rate
                    principal_payment = 0 if period < total_periods else principal
                    remaining_balance = principal - principal_payment
                    
                    schedule.append({
                        'period': period,
                        'payment': interest_payment + principal_payment,
                        'principal': principal_payment,
                        'interest': interest_payment,
                        'balance': max(0, remaining_balance)
                    })
            
            return schedule
        
        schedule = calculate_amortization_schedule(
            loan['amount'],
            loan['rate'],
            loan_term_years,
            payment_frequency,
            amortization_type
        )
        
        # ==================== AMORTIZATION SCHEDULE TABLE ====================
        
        st.subheader("Detailed Amortization Schedule")
        
        # Display summary
        total_interest = sum(s['interest'] for s in schedule)
        total_payments = sum(s['payment'] for s in schedule)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Payments", f"£{total_payments/1e6:.2f}M")
        
        with col2:
            st.metric("Total Interest", f"£{total_interest/1e6:.2f}M")
        
        with col3:
            interest_pct = (total_interest / loan['amount']) * 100
            st.metric("Interest as % of Principal", f"{interest_pct:.1f}%")
        
        with col4:
            st.metric("Number of Periods", len(schedule))
        
        # Create table with first 12 periods shown, rest can be scrolled
        schedule_df_data = []
        for s in schedule:
            schedule_df_data.append({
                'Period': s['period'],
                'Payment (£)': f"{s['payment']:,.0f}",
                'Principal (£)': f"{s['principal']:,.0f}",
                'Interest (£)': f"{s['interest']:,.0f}",
                'Balance (£)': f"{s['balance']:,.0f}"
            })
        
        schedule_df = pl.DataFrame(schedule_df_data)
        
        st.dataframe(schedule_df, width=1200, height=500)
        
        # ==================== VISUALIZATIONS ====================
        
        st.subheader("Amortization Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Principal vs Interest over time
            fig_payment = go.Figure()
            
            fig_payment.add_trace(go.Scatter(
                x=[s['period'] for s in schedule],
                y=[s['principal'] for s in schedule],
                name='Principal Payment',
                fill='tozeroy',
                mode='lines'
            ))
            
            fig_payment.add_trace(go.Scatter(
                x=[s['period'] for s in schedule],
                y=[s['interest'] for s in schedule],
                name='Interest Payment',
                fill='tonexty',
                mode='lines'
            ))
            
            fig_payment.update_layout(
                title='Payment Composition Over Time',
                xaxis_title='Period',
                yaxis_title='Payment Amount (£)',
                hovermode='x unified',
                height=450,
                width=600
            )
            
            st.plotly_chart(fig_payment, width=900)
        
        with col2:
            # Remaining balance over time
            fig_balance = go.Figure()
            
            fig_balance.add_trace(go.Scatter(
                x=[s['period'] for s in schedule],
                y=[s['balance'] for s in schedule],
                name='Remaining Balance',
                fill='tozeroy',
                mode='lines+markers',
                line=dict(color='#1f77b4')
            ))
            
            fig_balance.update_layout(
                title='Remaining Balance Over Time',
                xaxis_title='Period',
                yaxis_title='Balance (£)',
                hovermode='x',
                height=450,
                width=600
            )
            
            st.plotly_chart(fig_balance, width=900)
        
        # ==================== COMPARISON WITH OTHER AMORTIZATION TYPES ====================
        
        st.subheader("Amortization Type Comparison")
        
        # Calculate all three types
        straight_line = calculate_amortization_schedule(
            loan['amount'], loan['rate'], loan_term_years, payment_frequency, "Straight-line"
        )
        annuity = calculate_amortization_schedule(
            loan['amount'], loan['rate'], loan_term_years, payment_frequency, "Annuity (Equal payments)"
        )
        bullet = calculate_amortization_schedule(
            loan['amount'], loan['rate'], loan_term_years, payment_frequency, "Bullet (Balloon)"
        )
        
        # Create comparison chart
        fig_comparison = go.Figure()
        
        fig_comparison.add_trace(go.Scatter(
            x=[s['period'] for s in straight_line],
            y=[s['payment'] for s in straight_line],
            name='Straight-line',
            mode='lines'
        ))
        
        fig_comparison.add_trace(go.Scatter(
            x=[s['period'] for s in annuity],
            y=[s['payment'] for s in annuity],
            name='Annuity (Equal)',
            mode='lines'
        ))
        
        fig_comparison.add_trace(go.Scatter(
            x=[s['period'] for s in bullet],
            y=[s['payment'] for s in bullet],
            name='Bullet',
            mode='lines'
        ))
        
        fig_comparison.update_layout(
            title='Payment Schedule Comparison by Amortization Type',
            xaxis_title='Period',
            yaxis_title='Payment Amount (£)',
            hovermode='x unified',
            height=450,
            width=1200
        )
        
        st.plotly_chart(fig_comparison, width=1200)
        
        # ==================== KEY METRICS ====================
        
        st.subheader("Key Metrics by Amortization Type")
        
        metrics_comparison = []
        
        for name, sched in [("Straight-line", straight_line), ("Annuity", annuity), ("Bullet", bullet)]:
            total_int = sum(s['interest'] for s in sched)
            avg_pmt = sum(s['payment'] for s in sched) / len(sched)
            max_pmt = max(s['payment'] for s in sched)
            min_pmt = min(s['payment'] for s in sched)
            
            metrics_comparison.append({
                'Type': name,
                'Total Interest': f"£{total_int/1e6:.2f}M",
                'Avg Payment': f"£{avg_pmt:,.0f}",
                'Max Payment': f"£{max_pmt:,.0f}",
                'Min Payment': f"£{min_pmt:,.0f}"
            })
        
        metrics_df = pl.DataFrame(metrics_comparison)
        st.dataframe(metrics_df, width=1200)
        
        # ==================== EXPORT OPTIONS ====================
        
        st.subheader("Export Schedule")
        
        # Convert schedule to CSV
        csv_data = "Period,Payment,Principal,Interest,Balance\n"
        for s in schedule:
            csv_data += f"{s['period']},{s['payment']:.2f},{s['principal']:.2f},{s['interest']:.2f},{s['balance']:.2f}\n"
        
        st.download_button(
            label="📥 Download Schedule as CSV",
            data=csv_data,
            file_name=f"Amortization_Schedule_{loan_id}.csv",
            mime="text/csv"
        )
