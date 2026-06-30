from pydantic import BaseModel
from typing import Optional

class AuditEventCreate(BaseModel):
    user_email: str
    event_type: str
    description: str
    ip_address: Optional[str] = None

class AuditEvent(AuditEventCreate):
    id: int
    timestamp: str

    class Config:
        from_attributes = True
