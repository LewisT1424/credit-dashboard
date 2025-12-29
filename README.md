# Credit Dashboard

A comprehensive Streamlit-based credit portfolio analysis dashboard with interactive visualizations, advanced analytics, and scenario testing capabilities.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Features

The dashboard provides 6 analytical pages:

- **Home** - Portfolio overview with KPI metrics, filters, and Excel export
- **Risk Analysis** - Portfolio risk metrics and status breakdown
- **Maturity Analysis** - Maturity profile, WAM, and refinancing risk
- **Concentration Risk** - Single-name and sector concentration analysis
- **Borrower Search** - Search and drill-down borrower analysis
- **Cash Flow Analysis** - Monthly cash flow projections (6-60 months)
- **Stress Testing** - Portfolio resilience under adverse scenarios

## Documentation

All implementation phases documented in dedicated summaries:

- **[Phase 1 - Quick Wins](docs/PHASE_1_SUMMARY.md)** - Portfolio overview and filtering
- **[Phase 2 - Medium Complexity](docs/PHASE_2_SUMMARY.md)** - Maturity and concentration analysis  
- **[Phase 3 - Advanced Analytics](docs/PHASE_3_SUMMARY.md)** - Borrower analysis, cash flows, stress testing

Full index: [docs/INDEX.md](docs/INDEX.md)

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running

Start the dashboard:
```bash
streamlit run Home.py
```

## Project Structure

```
credit-dashboard/
├── Home.py                    # Main portfolio overview page
├── pages/                     # Analysis pages
│   ├── 1_Risk_Analysis.py
│   ├── 2_Maturity_Analysis.py
│   ├── 3_Concentration_Risk.py
│   ├── 4_Borrower_Search.py
│   ├── 5_Cash_Flow_Analysis.py
│   └── 6_Stress_Testing.py
├── utils.py                   # 12 shared utility functions
├── requirements.txt           # Python dependencies
├── docs/                      # Phase documentation
│   ├── PHASE_1_SUMMARY.md
│   ├── PHASE_2_SUMMARY.md
│   ├── PHASE_3_SUMMARY.md
│   └── INDEX.md
└── data/                      # Sample data directory
```

## Data Format

Upload a CSV file with the following columns:

- `loan_id` - Unique loan identifier
- `borrower` - Borrowing entity name
- `amount` - Loan amount (£)
- `rate` - Interest rate (%)
- `rating` - Credit rating
- `sector` - Industry sector
- `status` - Loan status (Performing, Non-Performing, Watch List)
- `maturity_date` - Maturity date (YYYY-MM-DD)

Sample data is provided in the `data/` directory for testing.

## Tech Stack

- Python 3.x
- Streamlit - Web framework
- Polars - Data processing
- Plotly - Interactive visualizations

## License

MIT
