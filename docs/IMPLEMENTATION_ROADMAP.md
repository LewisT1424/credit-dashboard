# Credit Dashboard - Implementation Roadmap

## Project Status Overview
- **Current Phase**: 3 (Complete)
- **Total Pages**: 6 functional pages
- **Total Lines of Code**: 1,904 (production Python)
- **Data Points**: 50 loans across 13 borrowers
- **Documentation Files**: 6 markdown files + this roadmap

---

## ✅ COMPLETED - Phases 1-3

### Phase 1: Foundation & Quick Wins
**Status**: ✅ COMPLETE | **Lines**: 354 | **Time**: Week 1

#### Features Implemented
1. **Portfolio Overview Dashboard** (Home.py)
   - Total portfolio metrics (count, exposure, avg rate)
   - Risk status distribution (pie chart)
   - Sector breakdown (bar chart)
   - KPI cards with visual indicators
   - Auto-loads sample data from `data/sample_portfolio.csv`
   - Interactive filters by sector, status, rating

2. **Excel Data Export**
   - Export current filtered portfolio to Excel
   - Maintains all loan details and formatting
   - Single-click download

3. **Professional UI Components**
   - Streamlit layout="wide" configuration
   - Color-coded KPI cards (red/green/yellow)
   - Responsive container design
   - Mobile-friendly dataframes

4. **Sample Data Integration**
   - 50 loans pre-loaded (£243M total portfolio)
   - Diverse sectors (13+ industries)
   - Credit ratings A to CCC+
   - Maturity dates 2025-2030

---

### Phase 2: Maturity & Concentration Analysis
**Status**: ✅ COMPLETE | **Lines**: 186 + 207 = 393 | **Time**: Week 2

#### Page 2: Maturity Analysis (2_Maturity_Analysis.py)
- **WAM Calculation** - Weighted Average Maturity
- **Quarterly Maturity Profile** - Distribution chart
- **Upcoming Maturities** - Next 90 days alert
- **Concentration by Maturity** - HHI calculation
- **Amortization Schedule** - Monthly repayment projection

#### Page 3: Concentration Risk (3_Concentration_Risk.py)
- **HHI Index** - Herfindahl-Hirschman concentration metric
- **Single-Name Concentration** - Top 10 borrowers exposure
- **Sector Concentration** - Portfolio diversification
- **Rating Distribution** - Credit quality concentration
- **Risk Heat Maps** - Visual concentration indicators

---

### Phase 3: Advanced Analytics
**Status**: ✅ COMPLETE | **Lines**: 137 + 195 + 251 = 583 | **Time**: Week 3

#### Page 4: Borrower Search & Drill-Down (4_Borrower_Search.py)
- **Searchable Selectbox** - All borrower names with search capability
- **Quick Results Table** - Loan details display
- **Detailed Drill-Down** - Individual borrower metrics
  - Total exposure & portfolio %
  - Number of loans & health %
  - Weighted average rate
  - Risk indicators (non-performing, high-risk, speculative)
- **Loan-Level Details** - Complete loan attributes by borrower
- **Fixed Issues**: 
  - Changed `rating` → `credit_rating` (column name fix)
  - Changed `isin()` → `is_in()` (Polars API)
  - Replaced `use_container_width` → `width` parameter (deprecated API)

#### Page 5: Cash Flow Analysis (5_Cash_Flow_Analysis.py)
- **Monthly Cash Flow Projection** - 6, 12, 24, 36, 60 month views
- **Principal & Interest Breakdown** - Stacked area charts
- **Cumulative Cash Flow** - Total inflow tracking
- **Scenario Selection** - Base/Stress/Growth scenarios
- **Interactive Charts** - Plotly visualization (width=1200)

#### Page 6: Stress Testing (6_Stress_Testing.py)
- **Scenario Analysis** - Base, Stress, Growth, Recession scenarios
- **Loss Estimation** - Default loss calculations
- **Recovery Rate Analysis** - Recovery assumptions by rating
- **Weighted Loss Impact** - Dollar impact visualization
- **Sensitivity Analysis** - Default rate sensitivity
- **Comparative Metrics** - Side-by-side scenario comparison

---

## Technical Foundation

### Architecture
```
credit-dashboard/
├── Home.py                          # Main portfolio overview
├── pages/
│   ├── 1_Risk_Analysis.py          # Risk metrics & status
│   ├── 2_Maturity_Analysis.py      # Maturity profile & WAM
│   ├── 3_Concentration_Risk.py     # HHI & concentration
│   ├── 4_Borrower_Search.py        # Borrower drill-down
│   ├── 5_Cash_Flow_Analysis.py     # Cash flow projections
│   └── 6_Stress_Testing.py         # Scenario analysis
├── utils.py                         # 12 utility functions
├── requirements.txt                 # 5 core dependencies
└── data/
    └── sample_portfolio.csv        # 50 loans, £243M
```

### Core Libraries
- **Streamlit 1.28+** - Web framework
- **Polars 0.19+** - Fast dataframe operations
- **Plotly 5.17+** - Interactive charts
- **openpyxl 3.11+** - Excel export
- **reportlab 4.0+** - PDF generation (framework ready)

### Key Functions (utils.py)
1. `load_sample_data()` - Load CSV data
2. `search_borrowers()` - Filter by name/loan_id
3. `get_borrower_detail()` - Aggregate borrower metrics
4. `calculate_wam()` - Weighted average maturity
5. `calculate_hhi()` - Concentration index
6. `calculate_cash_flows()` - Monthly projections
7. `apply_stress_scenario()` - Scenario modifications
8. `export_to_excel()` - Excel export with formatting
9. Plus 4 more supporting functions

### Session State
- **Key**: `st.session_state.portfolio_data`
- **Type**: Polars DataFrame
- **Columns**: 8 (loan_id, borrower, amount, rate, sector, maturity_date, credit_rating, status)
- **Auto-Load**: Checkbox defaults to True on Home page

---

## 📋 PLANNED - Future Phases

### Phase 4: Quick Wins (Est. 2-3 hours)
*These are 20-30 minute features with high user value*

#### 4.1 Portfolio Health Dashboard
- **Purpose**: Single view of overall portfolio health
- **Features**:
  - Composite health score (0-100)
  - Risk heat map by borrower
  - Traffic light status indicators
  - Key risk drivers highlighted
- **Time Est**: 30 min
- **Dependencies**: Current data structure
- **Data Fields Needed**: None (existing data sufficient)

#### 4.2 Watch List Management
- **Purpose**: Track and monitor risky loans separately
- **Features**:
  - Dedicated watch list view
  - Separate metrics for watch list
  - Action required alerts
  - Watch list drill-down
- **Time Est**: 25 min
- **Dependencies**: New page file
- **Data Fields Needed**: None (status field already has "Watch List")

#### 4.3 Loan Amortization Details
- **Purpose**: View payment schedules per loan
- **Features**:
  - Monthly payment breakdown
  - Principal/interest split
  - Remaining balance tracking
  - Payment calendar view
- **Time Est**: 30 min
- **Dependencies**: New page, calculation logic
- **Data Fields Needed**: Loan term (years) - can be calculated from maturity_date

#### 4.4 Comparative Analysis
- **Purpose**: Compare current vs historical portfolios
- **Features**:
  - Portfolio snapshots
  - Period-over-period changes
  - Risk migration analysis
  - Growth/decline metrics
- **Time Est**: 35 min
- **Dependencies**: CSV snapshot storage or database
- **Data Fields Needed**: Timestamp field, historical snapshots

#### 4.5 Report Generation (PDF Export)
- **Purpose**: Professional PDF reports for stakeholders
- **Features**:
  - PDF formatting with charts
  - Custom report sections
  - Executive summary
  - Detailed metrics tables
- **Time Est**: 40 min
- **Dependencies**: reportlab (already in requirements.txt)
- **Data Fields Needed**: None (existing data sufficient)

---

### Phase 5: Medium Complexity (Est. 3-4 hours)
*These are 45-90 minute features requiring logic/calculation*

#### 5.1 Default Probability Model
- **Purpose**: Estimate PD by credit rating
- **Features**:
  - Historical default rates by rating
  - Current portfolio PD calculation
  - Risk-weighted exposure
  - Rating-based filtering
- **Time Est**: 60 min
- **Dependencies**: Default rate assumptions table
- **Data Fields Needed**: Historical default data (new CSV)

#### 5.2 Geographic Analysis
- **Purpose**: Portfolio analysis by region
- **Features**:
  - Map visualization by country
  - Regional concentration metrics
  - Country risk exposure
  - Geographic heat map
- **Time Est**: 75 min
- **Dependencies**: New data field (country/region)
- **Data Fields Needed**: country column in CSV, mapping library (folium)

#### 5.3 Rating Migration Trends
- **Purpose**: Track how ratings change over time
- **Features**:
  - Rating transition matrix
  - Migration trends chart
  - Upgrade/downgrade counts
  - Historical rating tracking
- **Time Est**: 60 min
- **Dependencies**: Historical rating data storage
- **Data Fields Needed**: Historical rating snapshots, date tracking

#### 5.4 Covenant Tracking
- **Purpose**: Monitor financial covenant compliance
- **Features**:
  - Covenant dashboard
  - Current compliance status
  - Covenant violation alerts
  - Covenant history
- **Time Est**: 70 min
- **Dependencies**: Covenant data storage
- **Data Fields Needed**: debt_to_equity, interest_coverage, leverage_ratio columns

#### 5.5 What-If Simulator
- **Purpose**: Adjust loan parameters and see impacts
- **Features**:
  - Interactive loan adjustment sliders
  - Real-time impact calculation
  - Multiple scenario comparison
  - Sensitivity analysis
- **Time Est**: 80 min
- **Dependencies**: None (existing data)
- **Data Fields Needed**: None (works with current data)

---

### Phase 6: Advanced Features (Est. 6+ hours)
*These are complex features requiring integration/modeling*

#### 6.1 Database Integration
- **Purpose**: Persistent data storage and historical tracking
- **Features**:
  - SQLite/PostgreSQL backend
  - Data versioning
  - Historical audit trail
  - Real-time updates
- **Time Est**: 120+ min
- **Dependencies**: SQL database, ORM (SQLAlchemy)
- **Data Fields Needed**: Timestamp, version tracking columns

#### 6.2 User Authentication
- **Purpose**: Role-based access control
- **Features**:
  - Login/logout system
  - Role-based dashboards
  - Audit logging
  - User preferences
- **Time Est**: 90+ min
- **Dependencies**: streamlit-authenticator, database
- **Data Fields Needed**: User/role management tables

#### 6.3 Monte Carlo Simulation
- **Purpose**: Probabilistic portfolio modeling
- **Features**:
  - Random default scenario generation
  - Loss distribution analysis
  - Value-at-Risk (VaR) calculation
  - Confidence interval bands
- **Time Est**: 150+ min
- **Dependencies**: numpy, scipy, advanced plotting
- **Data Fields Needed**: Correlation matrix, default probability distributions

#### 6.4 API Integration
- **Purpose**: Connect to external data sources
- **Features**:
  - Real-time credit rating feeds
  - Market data integration
  - Economic indicator feeds
  - Automated data refresh
- **Time Est**: 120+ min
- **Dependencies**: API clients (yfinance, etc.)
- **Data Fields Needed**: API credentials, external data schema

#### 6.5 Real-time Alerts
- **Purpose**: Proactive notification system
- **Features**:
  - Risk threshold alerts
  - Email notifications
  - Dashboard notifications
  - Alert history
- **Time Est**: 100+ min
- **Dependencies**: Email service, alert rules engine
- **Data Fields Needed**: Threshold settings, user email list

---

## Implementation Priority Matrix

### High Value, Low Effort (Do Next!)
1. **Report Generation (PDF)** - 40 min, high stakeholder value
2. **Watch List Management** - 25 min, operational value
3. **Portfolio Health Dashboard** - 30 min, executive summary need
4. **Loan Amortization** - 30 min, borrower detail value

### High Value, Medium Effort (Plan for Phase 4)
5. **What-If Simulator** - 80 min, strategic value
6. **Default Probability Model** - 60 min, risk assessment
7. **Comparative Analysis** - 35 min, trend analysis

### Strategic (Plan for Phase 5+)
8. **Database Integration** - 120+ min, foundational
9. **User Authentication** - 90+ min, enterprise readiness
10. **Monte Carlo Simulation** - 150+ min, advanced risk modeling

---

## Data Requirements Summary

### Current Data Available
✅ loan_id, borrower, amount, rate, sector, maturity_date, credit_rating, status

### Data Needed for Future Phases
- **Geographic Analysis**: country, region fields
- **Covenant Tracking**: debt_to_equity, interest_coverage, leverage_ratio
- **Amortization Details**: term_years, origination_date
- **Historical Analysis**: snapshot_date, version field
- **Default Modeling**: historical_default_rate column or separate lookup table
- **Database Integration**: unique_loan_key, created_date, updated_date

---

## Testing & Validation Checklist

- [ ] All 6 pages load without errors
- [ ] Sample data auto-loads on Home page startup
- [ ] Session state (portfolio_data) accessible from all pages
- [ ] Excel export creates valid file with formatting
- [ ] All Polars dataframe operations execute without column errors
- [ ] Charts render correctly in all browsers
- [ ] Responsive design works on tablet/mobile
- [ ] No deprecated Streamlit API warnings
- [ ] Error handling displays user-friendly messages

---

## Version History

| Phase | Date | Pages | Features | Status |
|-------|------|-------|----------|--------|
| 1 | Week 1 | Home | Portfolio Overview, Filters, Excel Export | ✅ Complete |
| 2 | Week 2 | 2-3 | Maturity Analysis, Concentration Risk | ✅ Complete |
| 3 | Week 3 | 4-6 | Borrower Search, Cash Flow, Stress Testing | ✅ Complete |
| 4 | TBD | 7+ | Quick Win Features | 📋 Planned |
| 5 | TBD | TBD | Medium Complexity Features | 📋 Planned |
| 6 | TBD | TBD | Advanced Features | 📋 Planned |

---

## Quick Reference: File Locations

| File | Lines | Purpose |
|------|-------|---------|
| Home.py | 354 | Portfolio overview & data management |
| pages/1_Risk_Analysis.py | 166 | Risk metrics dashboard |
| pages/2_Maturity_Analysis.py | 186 | Maturity profile analysis |
| pages/3_Concentration_Risk.py | 207 | Concentration metrics |
| pages/4_Borrower_Search.py | 145 | Borrower drill-down |
| pages/5_Cash_Flow_Analysis.py | 195 | Cash flow projections |
| pages/6_Stress_Testing.py | 251 | Scenario analysis |
| utils.py | 250+ | 12+ utility functions |
| data/sample_portfolio.csv | 50 loans | Sample dataset |
| docs/ | 6 files | All documentation |

---

## Next Steps When Resuming Development

1. **Pick from Phase 4 Quick Wins** - Start with PDF Report Generation or Watch List Management
2. **Update sample_portfolio.csv** - Add new data fields as needed
3. **Create new page file** - e.g., `pages/7_Portfolio_Health.py`
4. **Add utility functions** - Extend utils.py with new calculations
5. **Test thoroughly** - Validate data flow and UI rendering
6. **Update documentation** - Add feature to IMPLEMENTATION_ROADMAP.md

---

*Last Updated: 2025-12-29*
*Next Review: When resuming Phase 4 development*
