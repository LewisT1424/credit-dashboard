# Phase 6: API Refactor & Azure Deployment - Implementation Plan

**Start Date**: January 2026  
**Target Completion**: March 2026 (8-10 weeks)  
**Status**: Planning Complete | Ready to Begin

---

## Executive Summary

Phase 6 transforms the credit dashboard from a single-user CSV-based application into a multi-user, cloud-deployed system with REST API backend and PostgreSQL database. This phase focuses on enterprise-grade architecture while maintaining the existing Streamlit frontend initially.

**Key Objectives:**
- Build FastAPI REST backend with JWT authentication
- Migrate data from CSV to PostgreSQL database
- Deploy to Azure with proper DevOps practices
- Support 30 total users (10 concurrent)
- Demonstrate production-ready cloud architecture for portfolio

**Non-Objectives (Future Phases):**
- React frontend replacement (Phase 7 - optional)
- Machine learning models (Phase 7 - optional)
- Advanced stress testing features (Phase 7 - optional)

---

## Architecture Overview

### Current State (Phase 5)
```
User Browser
    ↓
Streamlit App (Home.py + 15 pages)
    ↓
CSV Files (sample_portfolio.csv, default_rates.csv, rating_history.csv)
    ↓
Local File System
```

### Target State (Phase 6)
```
User Browser
    ↓
Streamlit Frontend (migrated to API calls)
    ↓ HTTP/REST (JWT Auth)
FastAPI Backend
    ↓ SQL (SQLAlchemy ORM)
PostgreSQL Database (Azure)
    ↓
Azure Storage (backups, logs)

Supporting Services:
- Azure Key Vault (secrets management)
- Application Insights (monitoring)
- GitHub Actions (CI/CD)
```

### Technology Stack

**Backend (NEW):**
- **FastAPI** 0.109+ - Modern Python web framework, async support, auto-generated API docs
- **SQLAlchemy** 2.0+ - Python ORM for database abstraction
- **Alembic** 1.13+ - Database migration tool
- **Pydantic** 2.5+ - Data validation and settings management
- **python-jose** 3.3+ - JWT token generation/validation
- **passlib** 1.7+ - Password hashing (bcrypt)
- **python-multipart** 0.0.6+ - File upload support

**Database:**
- **PostgreSQL** 15+ - Relational database (Azure Database for PostgreSQL)
- **psycopg2-binary** 2.9+ - PostgreSQL adapter for Python

**Frontend (Existing, Modified):**
- **Streamlit** 1.52.2 - Keep existing, add API client
- **requests** 2.31+ - HTTP client for API calls
- **Polars** 1.36.1 - Keep for data processing

**DevOps & Infrastructure:**
- **Docker** - Containerization
- **Docker Compose** - Local development orchestration
- **GitHub Actions** - CI/CD pipeline
- **Azure CLI** - Azure resource management
- **pytest** 7.4+ - Testing framework
- **httpx** 0.25+ - Async HTTP client for testing

**Azure Services:**
- **Azure App Service** - Host FastAPI backend
- **Azure Database for PostgreSQL** - Managed database
- **Azure Key Vault** - Secrets management
- **Application Insights** - Monitoring and logging
- **Azure Container Registry** - Docker image storage

---

## Database Schema Design

### Tables Overview

**Core Tables:**
1. `users` - User accounts and authentication
2. `portfolios` - Portfolio metadata
3. `loans` - Loan records (main data)
4. `default_rates` - Credit rating lookup table
5. `rating_history` - Historical rating changes
6. `audit_logs` - Change tracking (who/what/when)

**Relationships:**
- One user can have multiple portfolios (1:N)
- One portfolio can have multiple loans (1:N)
- Loans reference default_rates (N:1)
- Loans have multiple rating_history records (1:N)

### Detailed Schema

#### 1. users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,  -- 'admin', 'portfolio_manager'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### 2. portfolios
```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_id, name)
);

CREATE INDEX idx_portfolios_owner ON portfolios(owner_id);
```

#### 3. loans
```sql
CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    loan_id VARCHAR(50) NOT NULL,  -- Business loan ID (e.g., "1", "2")
    borrower VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    rate DECIMAL(5, 2) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    maturity_date DATE NOT NULL,
    credit_rating VARCHAR(10) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'Performing', 'Non-Performing', 'Watch List'
    country VARCHAR(100),
    debt_to_equity DECIMAL(10, 2),
    interest_coverage DECIMAL(10, 2),
    leverage_ratio DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, loan_id)
);

CREATE INDEX idx_loans_portfolio ON loans(portfolio_id);
CREATE INDEX idx_loans_rating ON loans(credit_rating);
CREATE INDEX idx_loans_sector ON loans(sector);
CREATE INDEX idx_loans_country ON loans(country);
CREATE INDEX idx_loans_status ON loans(status);
```

#### 4. default_rates
```sql
CREATE TABLE default_rates (
    id SERIAL PRIMARY KEY,
    credit_rating VARCHAR(10) UNIQUE NOT NULL,
    default_probability DECIMAL(10, 6) NOT NULL,
    recovery_rate DECIMAL(5, 4) NOT NULL,
    risk_weight DECIMAL(6, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_default_rates_rating ON default_rates(credit_rating);
```

#### 5. rating_history
```sql
CREATE TABLE rating_history (
    id SERIAL PRIMARY KEY,
    loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    credit_rating VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(loan_id, snapshot_date)
);

CREATE INDEX idx_rating_history_loan ON rating_history(loan_id);
CREATE INDEX idx_rating_history_date ON rating_history(snapshot_date);
```

#### 6. audit_logs
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,  -- 'CREATE', 'UPDATE', 'DELETE', 'LOGIN'
    entity_type VARCHAR(50) NOT NULL,  -- 'loan', 'portfolio', 'user'
    entity_id INTEGER,
    changes JSONB,  -- Store before/after state
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

---

## API Endpoint Specification

### Base URL
- **Local Development**: `http://localhost:8000`
- **Production**: `https://credit-dashboard-api.azurewebsites.net`

### Authentication Endpoints

#### POST /auth/register
Register a new user (admin only in production).

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "portfolio_manager"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "portfolio_manager",
  "created_at": "2026-01-15T10:30:00Z"
}
```

#### POST /auth/login
Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "john_doe",
    "role": "portfolio_manager"
  }
}
```

#### GET /auth/me
Get current authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "portfolio_manager",
  "last_login": "2026-01-15T10:30:00Z"
}
```

---

### Portfolio Endpoints

#### GET /portfolios
List all portfolios (filtered by user role).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "UK Corporate Portfolio",
    "description": "UK corporate lending portfolio",
    "owner_id": 1,
    "loan_count": 50,
    "total_exposure": 240800000,
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

#### POST /portfolios
Create a new portfolio.

**Request:**
```json
{
  "name": "European SME Portfolio",
  "description": "Small and medium enterprise loans across Europe"
}
```

**Response (201):**
```json
{
  "id": 2,
  "name": "European SME Portfolio",
  "description": "Small and medium enterprise loans across Europe",
  "owner_id": 1,
  "created_at": "2026-01-15T11:00:00Z"
}
```

#### GET /portfolios/{portfolio_id}
Get portfolio details.

**Response (200):**
```json
{
  "id": 1,
  "name": "UK Corporate Portfolio",
  "description": "UK corporate lending portfolio",
  "owner_id": 1,
  "loan_count": 50,
  "total_exposure": 240800000,
  "average_rating": "BBB",
  "created_at": "2026-01-15T10:00:00Z"
}
```

#### DELETE /portfolios/{portfolio_id}
Delete a portfolio (cascade deletes all loans).

**Response (204):** No content

---

### Loan Endpoints

#### GET /portfolios/{portfolio_id}/loans
Get all loans in a portfolio.

**Query Parameters:**
- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100) - Items per page
- `rating` (string, optional) - Filter by credit rating
- `sector` (string, optional) - Filter by sector
- `status` (string, optional) - Filter by status

**Response (200):**
```json
{
  "total": 50,
  "skip": 0,
  "limit": 100,
  "loans": [
    {
      "id": 1,
      "loan_id": "1",
      "borrower": "Acme Corp",
      "amount": 5000000.00,
      "rate": 4.50,
      "sector": "Technology",
      "maturity_date": "2030-12-31",
      "credit_rating": "BBB",
      "status": "Performing",
      "country": "United Kingdom",
      "debt_to_equity": 2.5,
      "interest_coverage": 3.2,
      "leverage_ratio": 3.1,
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

#### POST /portfolios/{portfolio_id}/loans
Create a single loan.

**Request:**
```json
{
  "loan_id": "51",
  "borrower": "New Corp Ltd",
  "amount": 3500000.00,
  "rate": 5.25,
  "sector": "Manufacturing",
  "maturity_date": "2028-06-30",
  "credit_rating": "BB+",
  "status": "Performing",
  "country": "Germany",
  "debt_to_equity": 2.1,
  "interest_coverage": 4.5,
  "leverage_ratio": 2.8
}
```

**Response (201):**
```json
{
  "id": 51,
  "loan_id": "51",
  "portfolio_id": 1,
  "borrower": "New Corp Ltd",
  ...
}
```

#### POST /portfolios/{portfolio_id}/loans/bulk
Bulk upload loans from CSV.

**Request (multipart/form-data):**
```
file: <CSV file>
```

**CSV Format:**
```csv
loan_id,borrower,amount,rate,sector,maturity_date,credit_rating,status,country,debt_to_equity,interest_coverage,leverage_ratio
52,Corp A,1000000,4.5,Technology,2029-12-31,BBB,Performing,UK,2.3,3.8,2.9
```

**Response (200):**
```json
{
  "total_rows": 100,
  "successful": 98,
  "failed": 2,
  "errors": [
    {
      "row": 15,
      "loan_id": "invalid",
      "error": "Amount must be positive"
    }
  ]
}
```

#### GET /portfolios/{portfolio_id}/loans/{loan_id}
Get single loan details.

**Response (200):**
```json
{
  "id": 1,
  "loan_id": "1",
  "borrower": "Acme Corp",
  ...
}
```

#### PATCH /portfolios/{portfolio_id}/loans/{loan_id}
Update a loan (partial update).

**Request:**
```json
{
  "credit_rating": "BBB+",
  "status": "Watch List"
}
```

**Response (200):**
```json
{
  "id": 1,
  "loan_id": "1",
  "credit_rating": "BBB+",
  "status": "Watch List",
  "updated_at": "2026-01-15T14:30:00Z",
  ...
}
```

#### DELETE /portfolios/{portfolio_id}/loans/{loan_id}
Delete a loan.

**Response (204):** No content

---

### Analytics Endpoints

#### GET /portfolios/{portfolio_id}/analytics/summary
Portfolio summary statistics.

**Response (200):**
```json
{
  "total_loans": 50,
  "total_exposure": 240800000.00,
  "average_rate": 4.73,
  "average_rating": "BBB",
  "weighted_average_maturity_months": 47.3,
  "performing_count": 42,
  "watch_list_count": 6,
  "non_performing_count": 2,
  "sector_breakdown": {
    "Technology": 12,
    "Manufacturing": 8,
    ...
  }
}
```

#### GET /portfolios/{portfolio_id}/analytics/default-probability
Default probability analysis.

**Response (200):**
```json
{
  "portfolio_pd": 0.0187,
  "expected_loss": 2320000.00,
  "risk_weighted_assets": 198450000.00,
  "top_risky_loans": [
    {
      "loan_id": "45",
      "borrower": "Risky Corp",
      "exposure": 4500000.00,
      "pd": 0.15,
      "expected_loss": 540000.00
    }
  ]
}
```

#### GET /portfolios/{portfolio_id}/analytics/concentration
Concentration risk metrics.

**Response (200):**
{
  "single_name_hhi": 0.0234,
  "sector_hhi": 0.1456,
  "country_hhi": 0.2103,
  "top_exposures": [...]
}
```

#### GET /portfolios/{portfolio_id}/analytics/covenant-compliance
Covenant breach analysis.

**Query Parameters:**
- `max_debt_to_equity` (float, default: 3.5)
- `min_interest_coverage` (float, default: 2.5)
- `max_leverage` (float, default: 4.0)

**Response (200):**
```json
{
  "total_breaches": 33,
  "debt_to_equity_breaches": 8,
  "interest_coverage_breaches": 11,
  "leverage_breaches": 14,
  "breached_loans": [...]
}
```

#### GET /portfolios/{portfolio_id}/analytics/rating-migration
Rating migration trends.

**Response (200):**
```json
{
  "transition_matrix": {
    "AAA": {"AAA": 0.95, "AA": 0.05, ...},
    ...
  },
  "upgrades": 12,
  "downgrades": 8,
  "fallen_angels": 2
}
```

---

### Admin Endpoints

#### GET /admin/users
List all users (admin only).

**Response (200):**
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "portfolio_manager",
    "is_active": true,
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

#### GET /admin/audit-logs
Get audit trail (admin only).

**Query Parameters:**
- `user_id` (int, optional)
- `action` (string, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `limit` (int, default: 100)

**Response (200):**
```json
{
  "total": 1523,
  "logs": [
    {
      "id": 1523,
      "user_id": 1,
      "username": "john_doe",
      "action": "UPDATE",
      "entity_type": "loan",
      "entity_id": 15,
      "changes": {
        "credit_rating": {"from": "BBB", "to": "BBB+"}
      },
      "created_at": "2026-01-15T14:30:00Z"
    }
  ]
}
```

---

## Security Implementation

### Authentication Flow

1. **User Login:**
   - User sends credentials to `/auth/login`
   - API validates username/password (hashed with bcrypt)
   - API generates JWT token (expires in 1 hour)
   - Token returned to client

2. **Authenticated Requests:**
   - Client includes `Authorization: Bearer <token>` header
   - API validates token signature and expiration
   - API extracts user ID from token payload
   - API checks user permissions for requested resource

3. **Token Refresh:**
   - Client can request new token with `/auth/refresh` before expiration
   - Or re-login if token expired

### JWT Token Structure

**Payload:**
```json
{
  "sub": "john_doe",
  "user_id": 1,
  "role": "portfolio_manager",
  "exp": 1705329600,
  "iat": 1705326000
}
```

**Algorithm:** HS256 (HMAC with SHA-256)  
**Secret:** Stored in Azure Key Vault

### Authorization Rules

**Role-Based Access Control:**

| Endpoint | Admin | Portfolio Manager |
|----------|-------|-------------------|
| POST /auth/register | ✓ | ✗ |
| GET /portfolios | All | Own only |
| POST /portfolios | ✓ | ✓ |
| DELETE /portfolios/{id} | ✓ | Own only |
| POST /loans | ✓ | Own portfolio |
| PATCH /loans/{id} | ✓ | Own portfolio |
| DELETE /loans/{id} | ✓ | Own portfolio |
| GET /analytics/* | ✓ | Own portfolio |
| GET /admin/* | ✓ | ✗ |

### Input Validation

**Pydantic Models** validate all incoming data:

```python
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import date

class LoanCreate(BaseModel):
    loan_id: str = Field(..., min_length=1, max_length=50)
    borrower: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, le=1_000_000_000)
    rate: Decimal = Field(..., ge=0, le=100)
    sector: str = Field(..., min_length=1, max_length=100)
    maturity_date: date
    credit_rating: str = Field(..., regex=r'^[A-D][A-D]?[A-D]?[+\-]?$')
    status: str = Field(..., regex=r'^(Performing|Non-Performing|Watch List)$')
    country: str | None = Field(None, max_length=100)
    debt_to_equity: Decimal | None = Field(None, ge=0, le=100)
    interest_coverage: Decimal | None = Field(None, ge=0, le=100)
    leverage_ratio: Decimal | None = Field(None, ge=0, le=100)
    
    @validator('maturity_date')
    def maturity_must_be_future(cls, v):
        if v < date.today():
            raise ValueError('Maturity date must be in the future')
        return v
```

### Rate Limiting

**Implementation:** SlowAPI middleware

**Limits:**
- General endpoints: 100 requests/minute per user
- Login endpoint: 5 requests/minute per IP (prevent brute force)
- Bulk upload: 10 requests/hour per user

### CORS Configuration

**Allowed Origins (Production):**
- `https://credit-dashboard.streamlit.app`
- `https://credit-dashboard.azurewebsites.net`

**Allowed Origins (Development):**
- `http://localhost:8501` (Streamlit)
- `http://localhost:3000` (React, if added later)

**Allowed Methods:** GET, POST, PATCH, DELETE, OPTIONS  
**Allowed Headers:** Authorization, Content-Type

### SQL Injection Prevention

- **SQLAlchemy ORM** used for all queries (parameterized by default)
- No raw SQL queries except in migrations
- Input validation prevents malicious payloads

### Secrets Management

**Azure Key Vault Secrets:**
- `jwt-secret-key` - JWT signing key
- `database-url` - PostgreSQL connection string
- `api-admin-password` - Initial admin password

**Local Development:**
- `.env` file (gitignored)
- Environment variables loaded with `python-dotenv`

---

## Azure Deployment Architecture

### Resource Group Structure

**Resource Group:** `rg-credit-dashboard-prod`

**Resources:**
1. **App Service Plan** - `asp-credit-dashboard-prod` (B1 tier, ~$13/month)
2. **App Service (API)** - `app-credit-api-prod`
3. **Azure Database for PostgreSQL** - `psql-credit-dashboard-prod` (B_Gen5_1, ~$30/month)
4. **Key Vault** - `kv-credit-dashboard`
5. **Container Registry** - `acrcreditdashboard`
6. **Application Insights** - `appi-credit-dashboard`
7. **Storage Account** - `stcreditdashboard` (backups, logs)

**Total Estimated Cost:** ~$50-60/month

### Deployment Flow

```
Developer pushes to GitHub
    ↓
GitHub Actions workflow triggered
    ↓
Run tests (pytest)
    ↓
Build Docker image
    ↓
Push to Azure Container Registry
    ↓
Deploy to Azure App Service
    ↓
Run database migrations (Alembic)
    ↓
Health check
    ↓
Update Application Insights
```

### Environment Variables (App Service)

```bash
DATABASE_URL=postgresql://user:pass@psql-credit-dashboard-prod.postgres.database.azure.com/creditdb
JWT_SECRET_KEY=@Microsoft.KeyVault(SecretUri=https://kv-credit-dashboard.vault.azure.net/secrets/jwt-secret-key)
ALLOWED_ORIGINS=https://credit-dashboard.streamlit.app
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Network Configuration

**App Service:**
- HTTPS only (enforced)
- Minimum TLS version: 1.2
- Public access (for demo purposes)
- VNet integration (optional, for future)

**PostgreSQL:**
- SSL required
- Firewall rules: Allow Azure services
- Public endpoint (secured with credentials)
- Automated backups enabled (7-day retention)

### Monitoring & Alerts

**Application Insights Metrics:**
- Request rate and response times
- Failed request rate
- Database query performance
- Exception tracking
- Custom events (login, bulk upload, etc.)

**Alerts:**
- API response time > 5 seconds (warning)
- Error rate > 5% (critical)
- Database CPU > 80% (warning)
- Failed login attempts > 10 in 5 minutes (security alert)

---

## Development Timeline

### Phase 6.1: Foundation & Setup (Weeks 1-2)

**Week 1: Local Development Environment**
- [ ] Set up project structure
- [ ] Create Docker Compose for local dev (FastAPI + PostgreSQL)
- [ ] Initialize FastAPI project with basic routing
- [ ] Set up Alembic for database migrations
- [ ] Create initial database schema
- [ ] Implement authentication (JWT)
- [ ] Write unit tests for auth

**Deliverable:** Working local API with authentication

**Week 2: Core API Endpoints**
- [ ] Implement user management endpoints
- [ ] Implement portfolio CRUD endpoints
- [ ] Implement loan CRUD endpoints
- [ ] Add input validation (Pydantic models)
- [ ] Implement authorization middleware
- [ ] Add rate limiting
- [ ] Write integration tests

**Deliverable:** Complete CRUD API with tests passing

### Phase 6.2: Data Migration & Analytics (Weeks 3-4)

**Week 3: Data Migration Tools**
- [ ] Write CSV → PostgreSQL migration script
- [ ] Migrate sample_portfolio.csv to database
- [ ] Migrate default_rates.csv to database
- [ ] Migrate rating_history.csv to database
- [ ] Implement bulk upload endpoint
- [ ] Add CSV validation logic
- [ ] Test with various CSV formats

**Deliverable:** All existing data in PostgreSQL

**Week 4: Analytics Endpoints**
- [ ] Implement portfolio summary analytics
- [ ] Implement default probability calculations
- [ ] Implement concentration risk metrics
- [ ] Implement covenant compliance endpoint
- [ ] Implement rating migration endpoint
- [ ] Optimize queries (indexes, joins)
- [ ] Performance testing (1000 loan dataset)

**Deliverable:** All 15 page analytics available via API

### Phase 6.3: Streamlit Migration (Weeks 5-6)

**Week 5: API Client Layer**
- [ ] Create API client module in Streamlit
- [ ] Implement authentication flow in Streamlit
- [ ] Add token storage in session_state
- [ ] Migrate Home.py to use API
- [ ] Migrate pages 1-5 to use API
- [ ] Add error handling and retry logic
- [ ] Implement caching strategy

**Deliverable:** Half of Streamlit pages using API

**Week 6: Complete Migration**
- [ ] Migrate pages 6-10 to use API
- [ ] Migrate pages 11-15 to use API
- [ ] Add loading states and spinners
- [ ] Implement manual refresh button
- [ ] Test multi-user scenarios locally
- [ ] Update documentation
- [ ] Remove CSV dependencies

**Deliverable:** Fully migrated Streamlit app

### Phase 6.4: Azure Deployment (Weeks 7-8)

**Week 7: Infrastructure Setup**
- [ ] Create Azure resource group
- [ ] Provision Azure Database for PostgreSQL
- [ ] Set up Azure Key Vault
- [ ] Create App Service and plan
- [ ] Configure Application Insights
- [ ] Set up Container Registry
- [ ] Configure environment variables
- [ ] Run database migrations on Azure

**Deliverable:** Azure infrastructure ready

**Week 8: CI/CD & Deployment**
- [ ] Create Dockerfile for FastAPI
- [ ] Set up GitHub Actions workflow
- [ ] Configure automated testing
- [ ] Deploy API to Azure App Service
- [ ] Deploy Streamlit (Streamlit Cloud or Azure)
- [ ] Configure custom domains (optional)
- [ ] Set up SSL certificates
- [ ] Configure monitoring and alerts

**Deliverable:** Live production deployment

### Phase 6.5: Testing & Documentation (Weeks 9-10)

**Week 9: Testing & Optimization**
- [ ] Load testing with 10 concurrent users
- [ ] Security audit (OWASP ZAP scan)
- [ ] Performance optimization
- [ ] Fix bugs from testing
- [ ] Database query optimization
- [ ] API response time improvements

**Deliverable:** Production-ready system

**Week 10: Documentation & Polish**
- [ ] API documentation (Swagger/ReDoc)
- [ ] Architecture diagrams
- [ ] Deployment runbook
- [ ] User guide for portfolio managers
- [ ] Developer setup guide
- [ ] Update README
- [ ] Create demo video/screenshots

**Deliverable:** Complete portfolio piece

---

## Testing Strategy

### Unit Tests
**Coverage Target:** 80%+

**Test Categories:**
- Authentication logic (JWT generation, validation)
- Authorization checks (role-based access)
- Input validation (Pydantic models)
- Database models (SQLAlchemy)
- Utility functions

**Tools:** pytest, pytest-cov

### Integration Tests
**Scope:**
- API endpoints (all CRUD operations)
- Database transactions
- Authentication flow
- File upload processing

**Approach:**
- Use test database (Docker container)
- Reset database between tests
- Mock external services (if any)

**Tools:** pytest, httpx (async client), pytest-asyncio

### Load Testing
**Scenarios:**
- 10 concurrent users
- 100 requests/minute
- Bulk upload of 1000 loans

**Metrics:**
- Response time (95th percentile < 2 seconds)
- Error rate (< 1%)
- Database connection pool usage

**Tools:** Locust or Artillery

### Security Testing
**Checks:**
- SQL injection attempts
- XSS in text fields
- CSRF protection
- JWT token validation
- Rate limiting effectiveness
- Dependency vulnerabilities

**Tools:** 
- OWASP ZAP
- Bandit (Python static analysis)
- pip-audit (dependency check)
- Safety (vulnerability scanner)

### Manual Testing
**Test Cases:**
- User registration and login
- Portfolio creation and deletion
- Loan CRUD operations
- CSV bulk upload (valid and invalid files)
- All 15 analytics endpoints
- Multi-user concurrent access
- Error scenarios (invalid tokens, missing data)

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk 1: Database Performance at Scale**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:** Index optimization, query profiling, connection pooling, read replicas (if needed)

**Risk 2: Azure Deployment Issues**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:** Test in staging environment first, Azure documentation, community support

**Risk 3: Security Vulnerabilities**
- **Probability:** Low-Medium
- **Impact:** High
- **Mitigation:** Security testing, dependency updates, code review, professional audit

**Risk 4: Streamlit API Integration Complexity**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:** Incremental migration, extensive testing, caching strategy

### Timeline Risks

**Risk 1: Learning Curve (Azure, FastAPI)**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:** Buffer time in schedule, comprehensive documentation, tutorials

**Risk 2: Scope Creep**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:** Stick to MVP features, defer enhancements to Phase 7

**Risk 3: Debugging Cloud Issues**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:** Comprehensive logging, Application Insights, local replication of issues

---

## Success Criteria

**Phase 6 is complete when:**

### Functional Requirements
- [ ] All 15 Streamlit pages work via API
- [ ] 30 users can be registered
- [ ] 10 concurrent users can access simultaneously
- [ ] CSV upload handles 1000 loans
- [ ] All analytics calculations match Phase 5 results
- [ ] Authentication and authorization work correctly
- [ ] Audit logging captures all changes

### Performance Requirements
- [ ] Portfolio overview loads in < 2 seconds
- [ ] Analytics endpoints respond in < 5 seconds
- [ ] Bulk upload of 100 loans completes in < 10 seconds
- [ ] API handles 100 requests/minute

### Quality Requirements
- [ ] 80%+ code coverage (unit tests)
- [ ] All integration tests passing
- [ ] Zero critical security vulnerabilities
- [ ] Error rate < 1% under load

### Deployment Requirements
- [ ] Live on Azure with HTTPS
- [ ] CI/CD pipeline working
- [ ] Application Insights monitoring enabled
- [ ] Automated backups configured
- [ ] Secrets in Azure Key Vault

### Documentation Requirements
- [ ] API documentation (Swagger)
- [ ] Architecture diagram
- [ ] Deployment runbook
- [ ] README updated
- [ ] Phase 6 summary document

---

## Tools & Resources

### Development Tools
- **IDE:** VS Code with extensions (Python, Docker, Azure Tools)
- **Database Client:** pgAdmin or DBeaver
- **API Testing:** Postman or Thunder Client
- **Git:** GitHub Desktop or CLI

### Documentation
- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Azure:** https://docs.microsoft.com/azure/
- **PostgreSQL:** https://www.postgresql.org/docs/

### Learning Resources
- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/
- Azure App Service: https://learn.microsoft.com/azure/app-service/
- Docker Compose: https://docs.docker.com/compose/
- GitHub Actions: https://docs.github.com/actions

---

## Next Steps

### Immediate Actions
1. Review and approve this planning document
2. Set up local development environment (Docker, PostgreSQL)
3. Initialize FastAPI project structure
4. Create GitHub repository structure
5. Start Week 1 tasks

### Questions to Resolve
- [ ] Streamlit deployment: Streamlit Cloud (free) or Azure Container?
- [ ] Domain name for production deployment?
- [ ] Initial admin user credentials strategy?

---

**Planning Document Version:** 1.0  
**Last Updated:** December 30, 2025  
**Status:** Ready for Development

**Next Document:** PHASE_6_WEEK_1_TASKS.md (to be created when starting)
