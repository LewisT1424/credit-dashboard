# Credit Dashboard

A comprehensive Streamlit-based credit portfolio analysis platform with 15 analytical pages, advanced credit risk analytics, and interactive scenario testing.

**Status**: Phase 5 Complete | Production Ready | 100% Validated

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run the Dashboard
```bash
streamlit run Home.py
```

The dashboard will open at `http://localhost:8501`

---

## Features Overview

### Dashboard Pages (15 Total)

#### Core Analytics (Pages 1-6)
- **Home** - Portfolio overview, KPI metrics, interactive filters, Excel export
- **Risk Analysis** - Portfolio risk metrics and status breakdown
- **Maturity Analysis** - Maturity profile, WAM calculation, refinancing risk
- **Concentration Risk** - Single-name and sector concentration (HHI analysis)
- **Borrower Search** - Borrower drill-down and detailed analysis
- **Cash Flow Analysis** - Monthly cash flow projections (6-60 months)

#### Advanced Analytics (Pages 7-11)
- **Portfolio Health** - Health score, problem loan identification, alerts
- **Watch List** - Monitoring tracked loans, trend analysis
- **Report Generation** - PDF and Excel report creation
- **Amortization Details** - Loan amortization schedule and prepayment analysis
- **What-If Simulator** - Scenario modeling and sensitivity analysis

#### Credit Risk Analytics (Pages 12-15) **NEW - Phase 5**
- **Default Probability Model** - Portfolio PD, expected loss, risk-weighted assets
- **Geographic Analysis** - Country exposure, HHI concentration, sector heatmaps
- **Covenant Tracking** - Real-time covenant compliance monitoring with breach alerts
- **Rating Migration Trends** - Credit rating transitions, migration patterns, fallen angels detection

---

## Key Capabilities

### Portfolio Analysis
- 50-loan portfolio with £240.8M total exposure
- 12 credit ratings (AAA to CCC+)
- 14 geographic regions (European countries)
- 12 economic sectors

### Risk Management
- **Default Probability**: Industry-standard PD curves by rating
- **Expected Loss**: Exposure × PD × (1 - Recovery Rate)
- **Covenant Compliance**: Configurable thresholds for D/E, Interest Coverage, Leverage
- **Geographic Risk**: Country concentration, sector diversification

### Advanced Analytics
- **Rating Migration**: 200 historical snapshots, transition matrix analysis
- **What-If Scenarios**: Adjust rates, spreads, defaults, prepayments
- **Stress Testing**: Portfolio resilience under adverse conditions
- **Cash Flow Projections**: 6-60 month projections with amortization

### Reporting
- Excel export with formatting
- PDF report generation
- CSV data export
- Custom filtering and sorting

---

## Data Structure

### Portfolio Data (`sample_portfolio.csv`)
**50 loans with 12 columns:**

**Original Fields:**
- `loan_id` - Unique loan identifier (1-50)
- `borrower` - Borrowing entity name
- `amount` - Loan amount (£, 1-10M range)
- `rate` - Interest rate (% per annum)
- `sector` - Industry sector (12 unique)
- `maturity_date` - Maturity date (YYYY-MM-DD)
- `credit_rating` - Credit rating (AAA to CCC+)
- `status` - Loan status (Performing, Non-Performing, Watch List)

**Phase 5 Additions:**
- `country` - Geographic location (14 European countries)
- `debt_to_equity` - Covenant ratio (1.5-5.8)
- `interest_coverage` - Covenant ratio (1.2-5.8)
- `leverage_ratio` - Covenant ratio (2.2-6.5)

### Lookup Tables (NEW - Phase 5)

**default_rates.csv** (14 credit ratings)
- Credit rating → default probability (0.1% to 100%)
- Credit rating → recovery rate (10% to 90%)
- Credit rating → risk weight (20% to 1250%)

**rating_history.csv** (200 snapshots)
- Loan rating history: 4 snapshots per loan
- Periods: 2024-01-31, 2024-07-31, 2025-01-31, 2025-07-31
- Used for migration analysis and trend detection

---

## Project Structure

```
credit-dashboard/
├── Home.py                           # Main dashboard
├── pages/                            # 15 Analytics pages
│   ├── 1_Risk_Analysis.py           # Risk metrics
│   ├── 2_Maturity_Analysis.py       # Maturity profile
│   ├── 3_Concentration_Risk.py      # Concentration analysis
│   ├── 4_Borrower_Search.py         # Borrower details
│   ├── 5_Cash_Flow_Analysis.py      # Cash flow projections
│   ├── 6_Stress_Testing.py          # Scenario testing
│   ├── 7_Portfolio_Health.py        # Health metrics (Phase 4)
│   ├── 8_Watch_List.py              # Monitoring (Phase 4)
│   ├── 9_Report_Generation.py       # Report export (Phase 4)
│   ├── 10_Amortization_Details.py   # Amortization (Phase 4)
│   ├── 11_What_If_Simulator.py      # Scenarios (Phase 4)
│   ├── 12_Default_Probability.py    # PD model (Phase 5)
│   ├── 13_Geographic_Analysis.py    # Geography (Phase 5)
│   ├── 14_Covenant_Tracking.py      # Covenants (Phase 5)
│   └── 15_Rating_Migration_Trends.py # Migration (Phase 5)
├── data/                            # Data files
│   ├── sample_portfolio.csv         # 50 loans, 12 columns
│   ├── sample_portfolio_backup.csv  # Original backup
│   ├── default_rates.csv            # PD/recovery lookup
│   └── rating_history.csv           # Rating history
├── docs/                            # Documentation
│   ├── PROJECT_SUMMARY.md           # Project overview
│   ├── PHASE_5_SUMMARY.md           # Phase 5 details
│   ├── VALIDATION_REPORT.md         # Test results
│   ├── IMPLEMENTATION_ROADMAP.md    # Complete roadmap
│   ├── PHASE_1-4_SUMMARY.md         # Historical phases
│   ├── INDEX.md                     # Documentation index
│   └── README.md                    # Quick start
├── utils.py                         # 12+ Utility functions
├── requirements.txt                 # Dependencies
└── .cleanuplog.txt                  # Cleanup record
```

---

## Technology Stack

### Framework & Data
- **Streamlit** 1.52.2 - Interactive web framework
- **Polars** 1.36.1 - High-performance data processing
- **Plotly** 6.5.0 - Interactive visualizations

### Supporting Libraries
- **Openpyxl** 3.1.5 - Excel export
- **XlsxWriter** 3.2.9 - Report generation
- **Python** 3.11+

### Optional
- **ReportLab** 4.0+ - PDF generation (optional, not required)

---

## Usage Examples

### Running the Dashboard
```bash
streamlit run Home.py
```

### Loading Custom Data
1. Navigate to Home page
2. Click "Upload CSV File"
3. Select your CSV with columns: loan_id, borrower, amount, rate, sector, maturity_date, credit_rating, status
4. Data persists across pages via session state

### Analyzing Default Risk (Page 12)
1. Go to "Default Probability Model"
2. Filter by credit rating, sector, or minimum PD%
3. View expected loss calculations
4. Export risk analysis to CSV

### Monitoring Covenants (Page 14)
1. Go to "Covenant Tracking"
2. Adjust thresholds (D/E, Interest Coverage, Leverage)
3. View breach summary and details
4. Get action item recommendations

### Analyzing Rating Changes (Page 15)
1. Go to "Rating Migration Trends"
2. View upgrade/downgrade distribution
3. Check transition matrix
4. Identify fallen angels and rising stars

---

## Sample Metrics

**Portfolio Overview:**
- Total Exposure: £240.8M
- Expected Loss: £2.32M (0.963% of portfolio)
- Covenant Breaches: 33 loans (8 D/E, 11 IC, 14 Leverage)
- Average Rating: BBB
- Countries: 14 European nations

---

## Validation & Quality

### Code Quality
- [PASS] 15 pages compiled (100% success)
- [PASS] 5,700+ lines of production Python
- [PASS] Comprehensive error handling
- [PASS] Zero unhandled exceptions

### Data Integrity
- [PASS] 4 data files validated
- [PASS] 100% join coverage (no nulls)
- [PASS] All calculations verified
- [PASS] Realistic data ranges

### Testing
- [PASS] All features tested
- [PASS] Edge cases handled
- [PASS] Performance optimized
- [PASS] User experience validated

---

## Documentation

### Quick References
- **[PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Complete project overview
- **[PHASE_5_SUMMARY.md](docs/PHASE_5_SUMMARY.md)** - Phase 5 implementation details
- **[VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)** - Comprehensive validation results
- **[IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)** - Full project roadmap

### Phase Documentation
- **[PHASE_1_SUMMARY.md](docs/PHASE_1_SUMMARY.md)** - Foundation features
- **[PHASE_2_SUMMARY.md](docs/PHASE_2_SUMMARY.md)** - Maturity & concentration
- **[PHASE_3_SUMMARY.md](docs/PHASE_3_SUMMARY.md)** - Borrower & cash flow
- **[PHASE_4_SUMMARY.md](docs/PHASE_4_SUMMARY.md)** - Portfolio management

### Documentation Index
- **[INDEX.md](docs/INDEX.md)** - Complete documentation index

---

## Deployment

### Pre-Deployment Checklist
- [PASS] All 15 pages compile successfully
- [PASS] All dependencies installed
- [PASS] Data files validated
- [PASS] Error handling comprehensive
- [PASS] Performance acceptable
- [PASS] Documentation complete

### Deploy to Production
```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run Home.py --logger.level=error
```

**Status**: READY FOR PRODUCTION DEPLOYMENT

---

## Configuration

### Streamlit Configuration (optional ~/.streamlit/config.toml)
```toml
[theme]
primaryColor = "#0066cc"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[client]
showErrorDetails = false
```

---

## Support

For detailed feature documentation, see:
- Individual page Python files in `pages/` directory
- Phase documentation in `docs/` directory
- Utility functions documentation in `utils.py`

---

## License

MIT License - See project documentation for details

---

**Last Updated**: December 30, 2025  
**Version**: Phase 5 Complete  
**Status**: Production Ready
