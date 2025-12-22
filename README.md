# Credit Fund Portfolio Dashboard

A web application for visualizing and analyzing credit fund loan portfolios. Built with Streamlit and designed for financial services professionals.

## Features

- Portfolio summary metrics (total value, loan count, weighted average yield)
- Top 5 largest exposures analysis
- Credit rating distribution and sector concentration
- Risk analysis with watch list and default tracking
- Interactive charts and data tables
- CSV upload functionality with sample data included

## Installation

1. Clone the repository:
```bash
git clone https://github.com/LewisT1424/credit-dashboard.git
cd credit-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application locally:
```bash
streamlit run Home.py
```

The app will open in your browser at `http://localhost:8501`

## CSV Format

Upload a CSV file with the following columns:

- `loan_id` - Unique identifier for each loan
- `borrower` - Name of the borrowing entity
- `amount` - Loan amount in £
- `rate` - Interest rate (%)
- `sector` - Industry sector
- `maturity_date` - Loan maturity date (YYYY-MM-DD)
- `credit_rating` - Credit rating (A, BBB, BB, B, CCC, etc.)
- `status` - Loan status (Active, Watch List, Defaulted)

Sample data is provided in the `data/` directory for testing.

## Tech Stack

- Python 3.x
- Streamlit - Web framework
- Polars - Data processing
- Plotly - Interactive visualizations

## License

MIT
