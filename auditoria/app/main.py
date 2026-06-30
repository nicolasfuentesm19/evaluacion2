import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from . import models, schemas, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Microservicio de Auditoría",
    description="API para el registro y monitoreo de eventos del sistema",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auditoria"}

@app.post("/events/", response_model=schemas.AuditEvent)
def create_event(event: schemas.AuditEventCreate, db: Session = Depends(database.get_db)):
    db_event = models.AuditEvent(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_email=event.user_email,
        event_type=event.event_type,
        description=event.description,
        ip_address=event.ip_address
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.get("/events/", response_model=List[schemas.AuditEvent])
def get_events(
    skip: int = 0, 
    limit: int = 100,
    event_type: Optional[str] = None,
    user_email: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.AuditEvent)
    if event_type:
        query = query.filter(models.AuditEvent.event_type == event_type)
    if user_email:
        query = query.filter(models.AuditEvent.user_email.ilike(f"%{user_email}%"))
    
    events = query.order_by(models.AuditEvent.id.desc()).offset(skip).limit(limit).all()
    return events
