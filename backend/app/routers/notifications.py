"""Notifications API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/")
async def list_notifications(notification_type: Optional[str] = None, is_read: Optional[bool] = None,
    severity: Optional[str] = None, limit: int = Query(50, le=200), offset: int = 0,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Notification).filter((Notification.user_id == current_user.id) | (Notification.user_id.is_(None)))
    if notification_type: q = q.filter(Notification.type == notification_type)
    if is_read is not None: q = q.filter(Notification.is_read == is_read)
    if severity: q = q.filter(Notification.severity == severity)
    total = q.count()
    notifs = q.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()
    return {"total": total, "notifications": [{"id": n.id, "type": n.type, "title": n.title,
        "message": n.message, "severity": n.severity, "is_read": n.is_read, "created_at": str(n.created_at)} for n in notifs]}

@router.get("/unread-count")
async def get_unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = db.query(Notification).filter((Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
        Notification.is_read == False).count()
    return {"unread_count": count}

@router.put("/{notification_id}/read")
async def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n: raise HTTPException(404, "Not found")
    n.is_read = True; db.commit(); return {"message": "Marked as read"}

@router.put("/read-all")
async def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter((Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
        Notification.is_read == False).update({Notification.is_read: True})
    db.commit(); return {"message": "All marked as read"}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n: raise HTTPException(404, "Not found")
    db.delete(n); db.commit(); return {"message": "Deleted"}
