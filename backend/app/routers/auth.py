"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5)
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=6)
    role: str = Field(default="analyst")

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RefreshRequest(BaseModel):
    refresh_token: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already taken")
    if req.role not in User.ROLES:
        raise HTTPException(400, f"Invalid role. Must be one of: {User.ROLES}")
    user = User(email=req.email, username=req.username, full_name=req.full_name,
                hashed_password=get_password_hash(req.password), role=req.role)
    db.add(user); db.commit(); db.refresh(user)
    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        db.add(AuditLog(action="login", resource="auth", status="failure",
                        details=f"Failed login for {req.email}",
                        ip_address=request.client.host if request.client else None))
        db.commit()
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")
    user.last_login = datetime.now(timezone.utc); db.commit()
    td = {"sub": str(user.id), "role": user.role}
    db.add(AuditLog(user_id=user.id, username=user.username, action="login", resource="auth",
                    status="success", ip_address=request.client.host if request.client else None))
    db.commit()
    return TokenResponse(access_token=create_access_token(td), refresh_token=create_refresh_token(td),
        user={"id": user.id, "email": user.email, "username": user.username, "full_name": user.full_name,
              "role": user.role, "department": user.department, "avatar_url": user.avatar_url})

@router.post("/refresh")
async def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return {"access_token": create_access_token({"sub": str(user.id), "role": user.role}), "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    return {"message": "If the email is registered, an OTP has been sent.", "dev_otp": "123456"}

@router.post("/reset-password")
async def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    if otp != "123456": raise HTTPException(400, "Invalid OTP")
    user = db.query(User).filter(User.email == email).first()
    if not user: raise HTTPException(404, "User not found")
    user.hashed_password = get_password_hash(new_password); db.commit()
    return {"message": "Password reset successfully"}

@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "username": current_user.username,
            "full_name": current_user.full_name, "role": current_user.role, "department": current_user.department,
            "phone": current_user.phone, "avatar_url": current_user.avatar_url, "is_active": current_user.is_active,
            "last_login": str(current_user.last_login) if current_user.last_login else None,
            "created_at": str(current_user.created_at)}

@router.put("/profile")
async def update_profile(req: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.full_name is not None: current_user.full_name = req.full_name
    if req.phone is not None: current_user.phone = req.phone
    if req.department is not None: current_user.department = req.department
    if req.avatar_url is not None: current_user.avatar_url = req.avatar_url
    db.commit(); return {"message": "Profile updated"}

@router.put("/change-password")
async def change_password(req: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    current_user.hashed_password = get_password_hash(req.new_password); db.commit()
    return {"message": "Password changed"}
