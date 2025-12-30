from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class RatingHistory(Base):
    """Rating history model for tracking credit rating changes over time."""
    
    __tablename__ = "rating_history"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    credit_rating = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    loan = relationship("Loan", back_populates="rating_history")
    
    def __repr__(self):
        return f"<RatingHistory(loan_id={self.loan_id}, date={self.snapshot_date}, rating='{self.credit_rating}')>"
