from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Loan(Base):
    """Loan model representing individual loan records."""
    
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    loan_id = Column(String(50), nullable=False)  # Business loan ID
    borrower = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    sector = Column(String(100), nullable=False, index=True)
    maturity_date = Column(Date, nullable=False)
    credit_rating = Column(String(10), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    
    # Phase 5 additions
    country = Column(String(100), nullable=True, index=True)
    debt_to_equity = Column(Numeric(10, 2), nullable=True)
    interest_coverage = Column(Numeric(10, 2), nullable=True)
    leverage_ratio = Column(Numeric(10, 2), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="loans")
    rating_history = relationship("RatingHistory", back_populates="loan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Loan(id={self.id}, loan_id='{self.loan_id}', borrower='{self.borrower}', amount={self.amount})>"
