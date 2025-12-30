from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class AuditLog(Base):
    """Audit log model for tracking all changes in the system."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN
    entity_type = Column(String(50), nullable=False, index=True)  # loan, portfolio, user
    entity_id = Column(Integer, nullable=True, index=True)
    changes = Column(JSON, nullable=True)  # Store before/after state
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', entity='{self.entity_type}')>"
