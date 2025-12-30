from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class LoanBase(BaseModel):
    """Base loan schema with common attributes."""
    loan_id: str = Field(..., min_length=1, max_length=50)
    borrower: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, le=Decimal('1000000000'))
    rate: Decimal = Field(..., ge=0, le=100)
    sector: str = Field(..., min_length=1, max_length=100)
    maturity_date: date
    credit_rating: str = Field(..., min_length=1, max_length=10)
    status: str = Field(..., min_length=1, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    debt_to_equity: Optional[Decimal] = Field(None, ge=0, le=100)
    interest_coverage: Optional[Decimal] = Field(None, ge=0, le=100)
    leverage_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    
    @validator('maturity_date')
    def maturity_must_be_future(cls, v):
        """Validate maturity date is in the future."""
        if v < date.today():
            raise ValueError('Maturity date must be in the future')
        return v
    
    @validator('status')
    def status_must_be_valid(cls, v):
        """Validate status is one of the allowed values."""
        allowed_statuses = ['Performing', 'Non-Performing', 'Watch List']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class LoanCreate(LoanBase):
    """Schema for creating a new loan."""
    pass


class LoanUpdate(BaseModel):
    """Schema for updating loan information."""
    borrower: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[Decimal] = Field(None, gt=0, le=Decimal('1000000000'))
    rate: Optional[Decimal] = Field(None, ge=0, le=100)
    sector: Optional[str] = Field(None, min_length=1, max_length=100)
    maturity_date: Optional[date] = None
    credit_rating: Optional[str] = Field(None, min_length=1, max_length=10)
    status: Optional[str] = Field(None, min_length=1, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    debt_to_equity: Optional[Decimal] = Field(None, ge=0, le=100)
    interest_coverage: Optional[Decimal] = Field(None, ge=0, le=100)
    leverage_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    
    @validator('status')
    def status_must_be_valid(cls, v):
        """Validate status if provided."""
        if v is not None:
            allowed_statuses = ['Performing', 'Non-Performing', 'Watch List']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class LoanInDB(LoanBase):
    """Schema for loan as stored in database."""
    id: int
    portfolio_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Loan(LoanInDB):
    """Schema for loan response."""
    pass


class LoanListResponse(BaseModel):
    """Schema for paginated loan list response."""
    total: int
    skip: int
    limit: int
    loans: list[Loan]


class BulkUploadResponse(BaseModel):
    """Schema for bulk upload response."""
    total_rows: int
    successful: int
    failed: int
    errors: list[dict]
