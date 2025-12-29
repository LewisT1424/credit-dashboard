"""
Shared utility functions for Credit Dashboard
"""
import polars as pl
import logging
from io import BytesIO
from datetime import date, timedelta

logger = logging.getLogger(__name__)


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

        return {
            'total_value': total_val,
            'num_of_loans': total_num,
            'avg_yield': weighted_yield,
            'avg_loan_size': avg_loan_size,
            'quality_mix': quality_mix
        }
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


def calculate_maturity_analysis(df):
    """Calculate maturity profile and related metrics"""
    try:
        # Check if maturity_date column exists
        if 'maturity_date' not in df.columns:
            return None
        
        # Parse dates and filter out invalid dates
        df_with_dates = df.with_columns([
            pl.col('maturity_date').str.strptime(pl.Date, "%Y-%m-%d").alias('maturity_parsed')
        ]).filter(pl.col('maturity_parsed').is_not_null())
        
        if len(df_with_dates) == 0:
            return None
        
        # Calculate Weighted Average Maturity (WAM) in years
        today = date(2025, 12, 29)
        today_pl = pl.lit(today)
        
        df_maturity = df_with_dates.with_columns([
            ((pl.col('maturity_parsed') - today_pl).dt.total_days() / 365.25).alias('years_to_maturity')
        ])
        
        total_amount = df_maturity['amount'].sum()
        wam = (df_maturity['amount'] * df_maturity['years_to_maturity']).sum() / total_amount
        
        # Group by year-quarter for maturity profile
        maturity_profile = df_maturity.with_columns([
            pl.col('maturity_parsed').dt.year().alias('year'),
            pl.col('maturity_parsed').dt.quarter().alias('quarter')
        ]).group_by(['year', 'quarter']).agg([
            pl.len().alias('count'),
            pl.col('amount').sum().alias('total_amount')
        ]).with_columns([
            (pl.col('total_amount') / 1e6).alias('amount_mm'),
            ((pl.col('total_amount') / total_amount) * 100).alias('pct_value'),
            (pl.col('year').cast(pl.Utf8) + '-Q' + pl.col('quarter').cast(pl.Utf8)).alias('period')
        ]).sort(['year', 'quarter'])
        
        # Upcoming maturities (next 12 months)
        months_12_date = today + timedelta(days=365)
        months_12 = pl.lit(months_12_date)
        
        upcoming_12m = df_maturity.filter(
            (pl.col('maturity_parsed') >= today_pl) & 
            (pl.col('maturity_parsed') <= months_12)
        ).select(['loan_id', 'borrower', 'amount', 'rate', 'maturity_parsed', 'credit_rating', 'sector'])
        
        # Upcoming maturities (next 6 months)
        months_6_date = today + timedelta(days=183)
        months_6 = pl.lit(months_6_date)
        
        upcoming_6m = df_maturity.filter(
            (pl.col('maturity_parsed') >= today_pl) & 
            (pl.col('maturity_parsed') <= months_6)
        ).select(['loan_id', 'borrower', 'amount', 'rate', 'maturity_parsed', 'credit_rating', 'sector'])
        
        return {
            'wam_years': wam,
            'maturity_profile': maturity_profile,
            'upcoming_6m': upcoming_6m,
            'upcoming_12m': upcoming_12m,
            'upcoming_6m_amount': upcoming_6m['amount'].sum() if len(upcoming_6m) > 0 else 0,
            'upcoming_12m_amount': upcoming_12m['amount'].sum() if len(upcoming_12m) > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error calculating maturity analysis: {str(e)}")
        return None


def calculate_concentration_metrics(df):
    """Calculate concentration risk metrics including Herfindahl index"""
    try:
        total_amount = df['amount'].sum()
        
        # Single name concentration (top 10)
        single_name_concentration = df.with_columns([
            ((pl.col('amount') / total_amount) * 100).alias('pct_portfolio')
        ]).select([
            'loan_id', 'borrower', 'amount', 'pct_portfolio', 'credit_rating', 'sector', 'status'
        ]).sort('amount', descending=True).head(10)
        
        # Check for concentration limit breaches (>10% single exposure)
        high_concentration = single_name_concentration.filter(pl.col('pct_portfolio') > 10.0)
        
        # Herfindahl-Hirschman Index (HHI) for sector concentration
        # HHI = sum of squared market shares (0-10,000 scale)
        sector_shares = df.group_by('sector').agg([
            pl.col('amount').sum().alias('total_amount')
        ]).with_columns([
            ((pl.col('total_amount') / total_amount) * 100).alias('pct_portfolio')
        ])
        
        hhi = (sector_shares['pct_portfolio'] ** 2).sum()
        
        # HHI interpretation
        if hhi < 1500:
            hhi_level = "Low Concentration"
            hhi_risk = "Low Risk"
        elif hhi < 2500:
            hhi_level = "Moderate Concentration"
            hhi_risk = "Medium Risk"
        else:
            hhi_level = "High Concentration"
            hhi_risk = "High Risk"
        
        # Borrower concentration by credit rating
        rating_concentration = df.group_by('credit_rating').agg([
            pl.len().alias('count'),
            pl.col('amount').sum().alias('total_amount')
        ]).with_columns([
            ((pl.col('total_amount') / total_amount) * 100).alias('pct_portfolio'),
            (pl.col('total_amount') / 1e6).alias('amount_mm')
        ]).sort('pct_portfolio', descending=True)
        
        return {
            'single_name_top10': single_name_concentration,
            'high_concentration_loans': high_concentration,
            'hhi_score': hhi,
            'hhi_level': hhi_level,
            'hhi_risk': hhi_risk,
            'rating_concentration': rating_concentration
        }
    except Exception as e:
        logger.error(f"Error calculating concentration metrics: {str(e)}")
        return None


def search_borrowers(df, search_query):
    """Search for borrowers by name or loan ID"""
    try:
        if not search_query or search_query.strip() == "":
            return df
        
        query_lower = search_query.lower()
        results = df.filter(
            pl.col('loan_id').str.to_lowercase().str.contains(query_lower) |
            pl.col('borrower').str.to_lowercase().str.contains(query_lower)
        )
        return results
    except Exception as e:
        logger.error(f"Error searching borrowers: {str(e)}")
        return df


def get_borrower_detail(df, borrower_name):
    """Get detailed information for a specific borrower"""
    try:
        borrower_loans = df.filter(pl.col('borrower') == borrower_name)
        if len(borrower_loans) == 0:
            return None
        
        total_exposure = borrower_loans['amount'].sum()
        num_loans = len(borrower_loans)
        avg_rate = (borrower_loans['amount'] * borrower_loans['rate']).sum() / total_exposure
        
        return {
            'borrower_name': borrower_name,
            'num_loans': num_loans,
            'total_exposure': total_exposure,
            'avg_rate': avg_rate,
            'loans': borrower_loans,
            'pct_of_portfolio': (total_exposure / df['amount'].sum()) * 100
        }
    except Exception as e:
        logger.error(f"Error getting borrower detail: {str(e)}")
        return None


def calculate_cash_flow_projection(df, months=24):
    """Calculate projected cash flows from interest and principal payments"""
    try:
        if 'maturity_date' not in df.columns:
            logger.warning("Cash flow projection requires maturity_date field")
            return None
        
        # Parse dates
        df_with_dates = df.with_columns([
            pl.col('maturity_date').str.strptime(pl.Date, "%Y-%m-%d").alias('maturity_parsed')
        ]).filter(pl.col('maturity_parsed').is_not_null())
        
        if len(df_with_dates) == 0:
            return None
        
        today = date(2025, 12, 29)
        cash_flows = []
        
        # Project monthly cash flows for next N months
        for month in range(months):
            month_date = today + timedelta(days=30*month)
            
            # Interest cash flows (monthly - assume 12x per year)
            monthly_interest = (df_with_dates['amount'] * df_with_dates['rate'] / 100 / 12).sum()
            
            # Principal repayments at maturity
            principal_repaid = df_with_dates.filter(
                pl.col('maturity_parsed').is_between(
                    month_date, 
                    month_date + timedelta(days=30)
                )
            )['amount'].sum()
            
            total_cash_flow = monthly_interest + principal_repaid
            
            cash_flows.append({
                'month': month + 1,
                'date': month_date,
                'interest_cf': monthly_interest / 1e6,
                'principal_cf': principal_repaid / 1e6,
                'total_cf': total_cash_flow / 1e6
            })
        
        return pl.DataFrame(cash_flows)
    except Exception as e:
        logger.error(f"Error calculating cash flow projection: {str(e)}")
        return None


def calculate_stress_test(df, scenarios):
    """Run stress test scenarios on portfolio"""
    try:
        base_case = {
            'total_value': df['amount'].sum() / 1e6,
            'num_loans': len(df),
            'avg_yield': (df['amount'] * df['rate']).sum() / df['amount'].sum(),
        }
        
        stress_results = []
        
        for scenario_name, params in scenarios.items():
            # Apply stress parameters
            stressed_df = df.clone()
            
            # Interest rate shock
            if 'rate_shock' in params:
                shock_bps = params['rate_shock']
                stressed_df = stressed_df.with_columns(
                    (pl.col('rate') + shock_bps / 100).alias('rate_stressed')
                )
                stressed_yield = (stressed_df['amount'] * stressed_df['rate_stressed']).sum() / stressed_df['amount'].sum()
            else:
                stressed_yield = base_case['avg_yield']
            
            # Default rate increase
            default_increase = params.get('default_increase', 0)
            estimated_defaults = df.height * (default_increase / 100)
            
            # Recovery rate assumption
            recovery_rate = params.get('recovery_rate', 100)
            
            # Calculate stressed metrics
            stressed_value = stressed_df['amount'].sum() / 1e6
            
            # Estimated loss from defaults
            avg_loan_size = df['amount'].mean()
            estimated_loss = estimated_defaults * avg_loan_size * (1 - recovery_rate / 100) / 1e6
            
            # Portfolio value after stress
            value_after_stress = stressed_value - estimated_loss
            
            stress_results.append({
                'scenario': scenario_name,
                'base_value': base_case['total_value'],
                'stressed_value': value_after_stress,
                'value_change': value_after_stress - base_case['total_value'],
                'pct_change': ((value_after_stress - base_case['total_value']) / base_case['total_value']) * 100,
                'base_yield': base_case['avg_yield'],
                'stressed_yield': stressed_yield,
                'estimated_defaults': int(estimated_defaults),
                'estimated_loss': estimated_loss
            })
        
        return pl.DataFrame(stress_results)
    except Exception as e:
        logger.error(f"Error calculating stress test: {str(e)}")
        return None
