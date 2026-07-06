"""Incident management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.incident import Incident
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

class IncidentCreate(BaseModel):
    type: str; title: str; description: Optional[str] = None; location: str
    intersection_id: Optional[str] = None; latitude: Optional[float] = None
    longitude: Optional[float] = None; severity: str = "medium"; priority: int = 3

class IncidentUpdate(BaseModel):
    status: Optional[str] = None; severity: Optional[str] = None
    priority: Optional[int] = None; description: Optional[str] = None; assigned_to: Optional[int] = None

@router.get("/")
async def list_incidents(status: Optional[str] = None, severity: Optional[str] = None,
    limit: int = Query(50, le=200), offset: int = 0,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Incident)
    if status: q = q.filter(Incident.status == status)
    if severity: q = q.filter(Incident.severity == severity)
    total = q.count()
    incidents = q.order_by(desc(Incident.created_at)).offset(offset).limit(limit).all()
    return {"total": total, "incidents": [{"id": i.id, "type": i.type, "title": i.title, "description": i.description,
        "location": i.location, "intersection_id": i.intersection_id, "latitude": i.latitude, "longitude": i.longitude,
        "severity": i.severity, "status": i.status, "priority": i.priority, "reported_by": i.reported_by,
        "assigned_to": i.assigned_to, "resolved_at": str(i.resolved_at) if i.resolved_at else None,
        "created_at": str(i.created_at), "updated_at": str(i.updated_at)} for i in incidents]}

@router.post("/", status_code=201)
async def create_incident(req: IncidentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inc = Incident(type=req.type, title=req.title, description=req.description, location=req.location,
        intersection_id=req.intersection_id, latitude=req.latitude, longitude=req.longitude,
        severity=req.severity, priority=req.priority, reported_by=current_user.id)
    db.add(inc)
    db.add(Notification(type="congestion", title=f"New Incident: {req.title}",
        message=f"{req.type.replace('_', ' ').title()} at {req.location}. Severity: {req.severity}.",
        severity="warning" if req.severity in ("low", "medium") else "critical"))
    db.commit(); db.refresh(inc); return {"message": "Incident created", "id": inc.id}

@router.put("/{incident_id}")
async def update_incident(incident_id: int, req: IncidentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc: raise HTTPException(404, "Incident not found")
    if req.status:
        inc.status = req.status
        if req.status == "resolved": inc.resolved_at = datetime.now(timezone.utc)
    if req.severity: inc.severity = req.severity
    if req.priority: inc.priority = req.priority
    if req.description: inc.description = req.description
    if req.assigned_to: inc.assigned_to = req.assigned_to
    db.commit(); return {"message": "Incident updated"}

@router.delete("/{incident_id}")
async def delete_incident(incident_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc: raise HTTPException(404, "Incident not found")
    db.delete(inc); db.commit(); return {"message": "Incident deleted"}
