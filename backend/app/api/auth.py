from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.db import get_db
from app.core.security import create_token, hash_password, verify_password
from app.models import User, UserPreference
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Email already registered")
    u = User(email=body.email.lower(), full_name=body.full_name, password_hash=hash_password(body.password))
    db.add(u)
    db.flush()
    db.add(UserPreference(user_id=u.id))
    db.commit()
    return TokenOut(access_token=create_token(str(u.id)))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == body.email.lower()))
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenOut(access_token=create_token(str(u.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
