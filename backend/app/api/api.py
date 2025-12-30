from fastapi import APIRouter
from app.api.endpoints import auth, portfolios

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])

# Placeholder for other routers (to be added in subsequent tasks)
# api_router.include_router(loans.router, prefix="/portfolios", tags=["loans"])
# api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
