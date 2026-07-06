"""Emergency vehicles API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.emergency_vehicle import EmergencyVehicle
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/api/emergency", tags=["Emergency"])

class EmergencyAlertRequest(BaseModel):
    vehicle_type: str
    call_sign: str
    destination_name: str
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    nearest_junction: Optional[str] = None
    notes: Optional[str] = None

@router.get("/vehicles")
async def get_vehicles(status: Optional[str] = None, vehicle_type: Optional[str] = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(EmergencyVehicle)
    if status: q = q.filter(EmergencyVehicle.status == status)
    if vehicle_type: q = q.filter(EmergencyVehicle.type == vehicle_type)
    vehicles = q.all()
    return {"vehicles": [{"id": v.id, "type": v.type, "call_sign": v.call_sign, "status": v.status,
        "current_lat": v.current_lat, "current_lng": v.current_lng, "destination_name": v.destination_name,
        "nearest_junction": v.nearest_junction, "eta_minutes": v.eta_minutes,
        "priority_active": v.priority_active, "dispatcher_notes": v.dispatcher_notes} for v in vehicles],
        "summary": {"total": len(vehicles), "available": sum(1 for v in vehicles if v.status == "available"),
            "dispatched": sum(1 for v in vehicles if v.status in ("dispatched", "en_route")),
            "on_scene": sum(1 for v in vehicles if v.status == "on_scene")}}

@router.post("/alert")
async def create_alert(req: EmergencyAlertRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(EmergencyVehicle).filter(EmergencyVehicle.call_sign == req.call_sign).first()
    if not v: raise HTTPException(404, "Vehicle not found")
    v.status = "dispatched"; v.destination_name = req.destination_name; v.priority_active = 1; v.eta_minutes = 10
    db.add(Notification(type="emergency", title=f"Emergency: {req.call_sign}",
        message=f"{req.vehicle_type.title()} {req.call_sign} dispatched to {req.destination_name}.", severity="critical"))
    db.commit(); return {"message": "Emergency alert created", "vehicle_id": v.id}

@router.put("/priority/{vehicle_id}")
async def toggle_priority(vehicle_id: int, activate: bool = True, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(EmergencyVehicle).filter(EmergencyVehicle.id == vehicle_id).first()
    if not v: raise HTTPException(404, "Vehicle not found")
    v.priority_active = 1 if activate else 0; db.commit()
    return {"message": f"Priority {'activated' if activate else 'deactivated'} for {v.call_sign}"}

@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vehicles = db.query(EmergencyVehicle).all()
    by_type = {}
    for v in vehicles:
        if v.type not in by_type: by_type[v.type] = {"total": 0, "available": 0, "active": 0}
        by_type[v.type]["total"] += 1
        if v.status == "available": by_type[v.type]["available"] += 1
        elif v.status in ("dispatched", "en_route", "on_scene"): by_type[v.type]["active"] += 1
    active = [v for v in vehicles if v.status in ("dispatched", "en_route", "on_scene")]
    return {"by_type": by_type, "active_emergencies": [{"id": v.id, "type": v.type, "call_sign": v.call_sign,
        "status": v.status, "destination": v.destination_name, "eta_minutes": v.eta_minutes,
        "nearest_junction": v.nearest_junction, "current_lat": v.current_lat, "current_lng": v.current_lng} for v in active],
        "total_vehicles": len(vehicles), "active_count": len(active),
        "priority_signals_active": sum(1 for v in vehicles if v.priority_active)}
