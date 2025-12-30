from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.loan import Loan
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    Portfolio as PortfolioSchema,
    PortfolioDetail
)
from app.api.endpoints.auth import get_current_user

router = APIRouter()


def check_portfolio_access(portfolio_id: int, current_user: User, db: Session) -> Portfolio:
    """
    Check if user has access to the portfolio.
    Admins can access any portfolio, portfolio managers only their own.
    
    Args:
        portfolio_id: Portfolio ID to check
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Portfolio: Portfolio object if access granted
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Admins can access all portfolios
    if current_user.role == "admin":
        return portfolio
    
    # Portfolio managers can only access their own
    if portfolio.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this portfolio"
        )
    
    return portfolio


@router.get("/", response_model=List[PortfolioSchema])
def list_portfolios(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all portfolios accessible to the current user.
    Admins see all portfolios, portfolio managers see only their own.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[Portfolio]: List of portfolios with loan count and total exposure
    """
    # Build query based on user role
    query = db.query(Portfolio)
    
    if current_user.role != "admin":
        query = query.filter(Portfolio.owner_id == current_user.id)
    
    portfolios = query.offset(skip).limit(limit).all()
    
    # Add computed fields
    result = []
    for portfolio in portfolios:
        loan_count = db.query(func.count(Loan.id)).filter(Loan.portfolio_id == portfolio.id).scalar()
        total_exposure = db.query(func.sum(Loan.amount)).filter(Loan.portfolio_id == portfolio.id).scalar() or 0
        
        portfolio_dict = {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "owner_id": portfolio.owner_id,
            "is_active": portfolio.is_active,
            "created_at": portfolio.created_at,
            "updated_at": portfolio.updated_at,
            "loan_count": loan_count,
            "total_exposure": float(total_exposure)
        }
        result.append(portfolio_dict)
    
    return result


@router.post("/", response_model=PortfolioSchema, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new portfolio owned by the current user.
    
    Args:
        portfolio_data: Portfolio creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Portfolio: Created portfolio object
        
    Raises:
        HTTPException: If portfolio name already exists for this user
    """
    # Check if portfolio name already exists for this user
    existing = db.query(Portfolio).filter(
        Portfolio.owner_id == current_user.id,
        Portfolio.name == portfolio_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio with this name already exists"
        )
    
    # Create new portfolio
    db_portfolio = Portfolio(
        name=portfolio_data.name,
        description=portfolio_data.description,
        owner_id=current_user.id,
        is_active=True
    )
    
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    
    # Return with computed fields
    return {
        "id": db_portfolio.id,
        "name": db_portfolio.name,
        "description": db_portfolio.description,
        "owner_id": db_portfolio.owner_id,
        "is_active": db_portfolio.is_active,
        "created_at": db_portfolio.created_at,
        "updated_at": db_portfolio.updated_at,
        "loan_count": 0,
        "total_exposure": 0.0
    }


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed portfolio information.
    
    Args:
        portfolio_id: Portfolio ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PortfolioDetail: Detailed portfolio information with metrics
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Calculate metrics
    loan_count = db.query(func.count(Loan.id)).filter(Loan.portfolio_id == portfolio.id).scalar()
    total_exposure = db.query(func.sum(Loan.amount)).filter(Loan.portfolio_id == portfolio.id).scalar() or 0
    
    # Status counts
    performing_count = db.query(func.count(Loan.id)).filter(
        Loan.portfolio_id == portfolio.id,
        Loan.status == "Performing"
    ).scalar()
    
    watch_list_count = db.query(func.count(Loan.id)).filter(
        Loan.portfolio_id == portfolio.id,
        Loan.status == "Watch List"
    ).scalar()
    
    non_performing_count = db.query(func.count(Loan.id)).filter(
        Loan.portfolio_id == portfolio.id,
        Loan.status == "Non-Performing"
    ).scalar()
    
    # Most common rating (simplified as average for now)
    average_rating = db.query(Loan.credit_rating).filter(
        Loan.portfolio_id == portfolio.id
    ).first()
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "owner_id": portfolio.owner_id,
        "is_active": portfolio.is_active,
        "created_at": portfolio.created_at,
        "updated_at": portfolio.updated_at,
        "loan_count": loan_count,
        "total_exposure": float(total_exposure),
        "average_rating": average_rating[0] if average_rating else None,
        "performing_count": performing_count,
        "watch_list_count": watch_list_count,
        "non_performing_count": non_performing_count
    }


@router.patch("/{portfolio_id}", response_model=PortfolioSchema)
def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update portfolio information.
    
    Args:
        portfolio_id: Portfolio ID
        portfolio_data: Portfolio update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Portfolio: Updated portfolio object
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Update fields if provided
    update_data = portfolio_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(portfolio, field, value)
    
    db.commit()
    db.refresh(portfolio)
    
    # Return with computed fields
    loan_count = db.query(func.count(Loan.id)).filter(Loan.portfolio_id == portfolio.id).scalar()
    total_exposure = db.query(func.sum(Loan.amount)).filter(Loan.portfolio_id == portfolio.id).scalar() or 0
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "owner_id": portfolio.owner_id,
        "is_active": portfolio.is_active,
        "created_at": portfolio.created_at,
        "updated_at": portfolio.updated_at,
        "loan_count": loan_count,
        "total_exposure": float(total_exposure)
    }


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a portfolio (cascade deletes all associated loans).
    
    Args:
        portfolio_id: Portfolio ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    db.delete(portfolio)
    db.commit()
    
    return None
