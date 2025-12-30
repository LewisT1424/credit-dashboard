# Week 2 Complete - Testing Guide

## What We Built
Week 2 deliverables are complete:
- ✅ 6 database models (User, Portfolio, Loan, DefaultRate, RatingHistory, AuditLog)
- ✅ Pydantic schemas with validation
- ✅ 14 API endpoints (3 auth + 5 portfolio + 6 loan)
- ✅ CSV bulk upload functionality
- ✅ Rate limiting (100/min global, 5/min login)
- ✅ Role-based authorization
- ✅ Database migration ready
- ✅ Basic test suite

## Next Steps

### Option 1: Test with Docker (Recommended for Production-like Testing)
```bash
# Install Docker if not already installed
sudo apt install docker.io docker-compose

# Start the services
cd backend
docker-compose up -d

# Wait for database to be ready (about 10 seconds)
sleep 10

# Apply database migration
alembic upgrade head

# View API documentation
# Open browser to: http://localhost:8000/docs
```

### Option 2: Test with SQLite (Quick Local Testing)
```bash
# Create a simple SQLite database for testing
cd backend

# Update .env file temporarily:
# DATABASE_URL=sqlite:///./test.db

# Apply migration (may need to modify for SQLite compatibility)
alembic upgrade head

# Run the API
uvicorn app.main:app --reload

# Open browser to: http://localhost:8000/docs
```

### Option 3: Manual Testing with cURL

After starting the API (with either option above):

```bash
# 1. Register a user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePass123!",
    "full_name": "Admin User",
    "role": "admin"
  }'

# 2. Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=SecurePass123!"

# Save the access_token from response

# 3. Create a portfolio
curl -X POST "http://localhost:8000/api/v1/portfolios" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Portfolio",
    "description": "My first portfolio"
  }'

# 4. Add a loan
curl -X POST "http://localhost:8000/api/v1/portfolios/1/loans" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_id": "LOAN001",
    "borrower": "ABC Corp",
    "amount": 1000000,
    "rate": 5.5,
    "sector": "Technology",
    "maturity_date": "2026-12-31",
    "credit_rating": "AA",
    "status": "performing",
    "country": "USA",
    "debt_to_equity": 0.5,
    "interest_coverage": 3.0,
    "leverage_ratio": 2.0
  }'
```

## API Endpoints Built

### Authentication (`/api/v1/auth`)
- `POST /register` - Create new user account
- `POST /login` - Get JWT token (rate limited: 5/minute)
- `GET /me` - Get current user info

### Portfolios (`/api/v1/portfolios`)
- `GET /` - List all portfolios (with pagination)
- `POST /` - Create new portfolio
- `GET /{id}` - Get portfolio details with metrics
- `PATCH /{id}` - Update portfolio
- `DELETE /{id}` - Delete portfolio (cascades to loans)

### Loans (`/api/v1/portfolios/{portfolio_id}/loans`)
- `GET /` - List loans (with filters: rating, sector, status)
- `POST /` - Create single loan
- `POST /bulk` - Upload CSV file with multiple loans
- `GET /{loan_id}` - Get loan details
- `PATCH /{loan_id}` - Update loan
- `DELETE /{loan_id}` - Delete loan

## Create Pull Request

Once you've tested locally and everything works:

```bash
# Push final changes
git push origin phase6-week2

# Go to GitHub and create PR:
# - Base: main
# - Compare: phase6-week2
# - Title: "Week 2: CRUD APIs, Database Migration, and Rate Limiting"
# - Description: Include the checklist from this README
```

## Week 2 Checklist
- ✅ Database models created (6 tables)
- ✅ Pydantic schemas with validation
- ✅ Portfolio CRUD endpoints (5)
- ✅ Loan CRUD endpoints (6)
- ✅ CSV bulk upload
- ✅ Rate limiting configured
- ✅ Authorization implemented
- ✅ Database migration created
- ⏳ Local testing (your task)
- ⏳ Pull request created (your task)
- ⏳ Merged to main (after review)

## What's Next: Week 3-4

After Week 2 is merged, we'll implement:
- Analytics endpoints (portfolio summary, default probability, concentration risk)
- Covenant compliance checking
- Rating migration matrix
- Admin audit log endpoint
- Performance optimization
