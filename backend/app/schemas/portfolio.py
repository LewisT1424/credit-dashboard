from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PortfolioBase(BaseModel):
    """Base portfolio schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio."""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating portfolio information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PortfolioInDB(PortfolioBase):
    """Schema for portfolio as stored in database."""
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Portfolio(PortfolioInDB):
    """Schema for portfolio response."""
    loan_count: Optional[int] = 0
    total_exposure: Optional[float] = 0.0


class PortfolioDetail(Portfolio):
    """Schema for detailed portfolio response with additional metrics."""
    average_rating: Optional[str] = None
    performing_count: Optional[int] = 0
    watch_list_count: Optional[int] = 0
    non_performing_count: Optional[int] = 0
