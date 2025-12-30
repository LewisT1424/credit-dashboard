# Backend API - FastAPI Application

This directory contains the FastAPI backend for the Credit Dashboard application.

## Project Structure

```
backend/
├── alembic/                 # Database migrations
│   ├── versions/            # Migration scripts
│   ├── env.py              # Alembic environment configuration
│   └── script.py.mako      # Migration template
├── app/
│   ├── api/
│   │   ├── endpoints/       # API route handlers
│   │   │   └── auth.py     # Authentication endpoints
│   │   └── api.py          # API router configuration
│   ├── core/
│   │   ├── config.py       # Application settings
│   │   └── security.py     # JWT and password utilities
│   ├── db/
│   │   └── session.py      # Database session management
│   ├── models/             # SQLAlchemy database models
│   │   └── user.py         # User model
│   ├── schemas/            # Pydantic schemas (request/response)
│   │   └── user.py         # User schemas
│   └── main.py             # FastAPI application entry point
├── tests/                  # Test files
├── .env.example            # Example environment variables
├── .gitignore             # Git ignore rules
├── alembic.ini            # Alembic configuration
├── Dockerfile             # Docker container definition
└── requirements.txt       # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and update the values:

```env
DATABASE_URL=postgresql://credituser:creditpass123@localhost:5432/creditdb
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
```

### 3. Start with Docker Compose (Recommended)

From the project root:

```bash
docker-compose up
```

This starts both PostgreSQL and the FastAPI application.

### 4. Run Database Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration with users table"

# Apply migrations
alembic upgrade head
```

### 5. Access the API

- **API Documentation (Swagger)**: http://localhost:8000/api/v1/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/api/v1/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

- **POST /api/v1/auth/register** - Register new user (admin only)
- **POST /api/v1/auth/login** - Login and get JWT token
- **GET /api/v1/auth/me** - Get current user info

### Example: Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "AdminPass123"}'
```

### Example: Authenticated Request

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Development

### Running Locally (without Docker)

1. Start PostgreSQL separately
2. Run the FastAPI development server:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest tests/ -v
```

### Running Tests with Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

## Database Migrations

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

### View Migration History

```bash
alembic history
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens are used for authentication
- Tokens expire after 60 minutes (configurable)
- CORS is configured for allowed origins
- Rate limiting is implemented on critical endpoints

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migration tool
- **Pydantic** - Data validation
- **PostgreSQL** - Database
- **python-jose** - JWT implementation
- **passlib** - Password hashing
- **uvicorn** - ASGI server

## Next Steps (Week 2)

- Add portfolio CRUD endpoints
- Add loan CRUD endpoints
- Implement analytics endpoints
- Add comprehensive tests
- Implement rate limiting

---

**Status**: Week 1 Foundation Complete  
**Last Updated**: December 30, 2025
