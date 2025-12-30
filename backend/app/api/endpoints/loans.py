from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import csv
import io
from decimal import Decimal
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.loan import Loan
from app.schemas.loan import (
    LoanCreate,
    LoanUpdate,
    Loan as LoanSchema,
    LoanListResponse,
    BulkUploadResponse
)
from app.api.endpoints.auth import get_current_user
from app.api.endpoints.portfolios import check_portfolio_access

router = APIRouter()


@router.get("/{portfolio_id}/loans", response_model=LoanListResponse)
def list_loans(
    portfolio_id: int,
    skip: int = 0,
    limit: int = 100,
    rating: Optional[str] = None,
    sector: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all loans in a portfolio with optional filtering.
    
    Args:
        portfolio_id: Portfolio ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        rating: Optional credit rating filter
        sector: Optional sector filter
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        LoanListResponse: Paginated list of loans
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Check portfolio access
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Build query with filters
    query = db.query(Loan).filter(Loan.portfolio_id == portfolio_id)
    
    if rating:
        query = query.filter(Loan.credit_rating == rating)
    if sector:
        query = query.filter(Loan.sector == sector)
    if status_filter:
        query = query.filter(Loan.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    loans = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "loans": loans
    }


@router.post("/{portfolio_id}/loans", response_model=LoanSchema, status_code=status.HTTP_201_CREATED)
def create_loan(
    portfolio_id: int,
    loan_data: LoanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new loan in a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        loan_data: Loan creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Loan: Created loan object
        
    Raises:
        HTTPException: If portfolio not found, access denied, or loan_id already exists
    """
    # Check portfolio access
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Check if loan_id already exists in this portfolio
    existing = db.query(Loan).filter(
        Loan.portfolio_id == portfolio_id,
        Loan.loan_id == loan_data.loan_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan with ID '{loan_data.loan_id}' already exists in this portfolio"
        )
    
    # Create new loan
    db_loan = Loan(
        portfolio_id=portfolio_id,
        **loan_data.dict()
    )
    
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    
    return db_loan


@router.get("/{portfolio_id}/loans/{loan_id}", response_model=LoanSchema)
def get_loan(
    portfolio_id: int,
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific loan by ID.
    
    Args:
        portfolio_id: Portfolio ID
        loan_id: Loan database ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Loan: Loan object
        
    Raises:
        HTTPException: If portfolio not found, access denied, or loan not found
    """
    # Check portfolio access
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Get loan
    loan = db.query(Loan).filter(
        Loan.id == loan_id,
        Loan.portfolio_id == portfolio_id
    ).first()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    return loan


@router.patch("/{portfolio_id}/loans/{loan_id}", response_model=LoanSchema)
def update_loan(
    portfolio_id: int,
    loan_id: int,
    loan_data: LoanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a loan.
    
    Args:
        portfolio_id: Portfolio ID
        loan_id: Loan database ID
        loan_data: Loan update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Loan: Updated loan object
        
    Raises:
        HTTPException: If portfolio not found, access denied, or loan not found
    """
    # Check portfolio access
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Get loan
    loan = db.query(Loan).filter(
        Loan.id == loan_id,
        Loan.portfolio_id == portfolio_id
    ).first()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Update fields if provided
    update_data = loan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(loan, field, value)
    
    db.commit()
    db.refresh(loan)
    
    return loan


@router.delete("/{portfolio_id}/loans/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    portfolio_id: int,
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a loan.
    
    Args:
        portfolio_id: Portfolio ID
        loan_id: Loan database ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If portfolio not found, access denied, or loan not found
    """
    # Check portfolio access
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Get loan
    loan = db.query(Loan).filter(
        Loan.id == loan_id,
        Loan.portfolio_id == portfolio_id
    ).first()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    db.delete(loan)
    db.commit()
    
    return None


@router.post("/{portfolio_id}/loans/bulk", response_model=BulkUploadResponse)
async def bulk_upload_loans(
    portfolio_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk upload loans from CSV file.
    
    Expected CSV format:
    loan_id,borrower,amount,rate,sector,maturity_date,credit_rating,status,country,debt_to_equity,interest_coverage,leverage_ratio
    
    Args:
        portfolio_id: Portfolio ID
        file: CSV file to upload
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BulkUploadResponse: Upload summary with success/failure counts
        
    Raises:
        HTTPException: If portfolio not found, access denied, or file is invalid
    """
    # Check portfolio access
    portfolio = check_portfolio_access(portfolio_id, current_user, db)
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    # Read file content
    contents = await file.read()
    decoded = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    total_rows = 0
    successful = 0
    failed = 0
    errors = []
    
    # Process each row
    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (row 1 is header)
        total_rows += 1
        
        try:
            # Check if loan_id already exists
            existing = db.query(Loan).filter(
                Loan.portfolio_id == portfolio_id,
                Loan.loan_id == row['loan_id']
            ).first()
            
            if existing:
                failed += 1
                errors.append({
                    "row": row_num,
                    "loan_id": row['loan_id'],
                    "error": "Loan ID already exists in portfolio"
                })
                continue
            
            # Parse and validate data
            loan_data = LoanCreate(
                loan_id=row['loan_id'],
                borrower=row['borrower'],
                amount=Decimal(row['amount']),
                rate=Decimal(row['rate']),
                sector=row['sector'],
                maturity_date=datetime.strptime(row['maturity_date'], '%Y-%m-%d').date(),
                credit_rating=row['credit_rating'],
                status=row['status'],
                country=row.get('country') or None,
                debt_to_equity=Decimal(row['debt_to_equity']) if row.get('debt_to_equity') else None,
                interest_coverage=Decimal(row['interest_coverage']) if row.get('interest_coverage') else None,
                leverage_ratio=Decimal(row['leverage_ratio']) if row.get('leverage_ratio') else None
            )
            
            # Create loan
            db_loan = Loan(
                portfolio_id=portfolio_id,
                **loan_data.dict()
            )
            
            db.add(db_loan)
            successful += 1
            
        except Exception as e:
            failed += 1
            errors.append({
                "row": row_num,
                "loan_id": row.get('loan_id', 'unknown'),
                "error": str(e)
            })
    
    # Commit all successful loans
    db.commit()
    
    return {
        "total_rows": total_rows,
        "successful": successful,
        "failed": failed,
        "errors": errors
    }
