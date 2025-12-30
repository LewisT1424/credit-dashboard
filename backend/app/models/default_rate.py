from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class DefaultRate(Base):
    """Default rate lookup table for credit ratings."""
    
    __tablename__ = "default_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_rating = Column(String(10), unique=True, nullable=False, index=True)
    default_probability = Column(Numeric(10, 6), nullable=False)
    recovery_rate = Column(Numeric(5, 4), nullable=False)
    risk_weight = Column(Numeric(6, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DefaultRate(rating='{self.credit_rating}', pd={self.default_probability})>"
