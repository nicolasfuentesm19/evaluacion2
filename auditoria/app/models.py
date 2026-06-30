from sqlalchemy import Column, Integer, String
from .database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, index=True)
    user_email = Column(String, index=True)
    event_type = Column(String, index=True)
    description = Column(String)
    ip_address = Column(String, nullable=True)
