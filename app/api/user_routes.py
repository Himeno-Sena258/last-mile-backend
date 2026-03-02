from fastapi import APIRouter, Request, status, Depends
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLogin
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_user,
    get_email,
    authenticate_user,
    get_current_user,
    Token,
)
from app.db.database import get_db
from app.models.user import User
from app.models.enums import UserRole

load_dotenv()

app = APIRouter()

@app.post('/api/users/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被注册")
    if user.email:
        db_email = get_email(db, user.email)
        if db_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        name=user.name,
        phone=user.phone,
        address=user.address,
        role=user.role,
        is_active=True,
        hashed_password=hashed_password,
        avatar_url=getattr(user, 'avatar_url', None),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post('/api/users/login', response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/api/users/me', response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.put('/api/users/me', response_model=UserResponse)
async def update_current_user(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_update.email is not None:
        existing = get_email(db, user_update.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册")
        current_user.email = user_update.email
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.address is not None:
        current_user.address = user_update.address
    if user_update.role is not None:
        current_user.role = user_update.role
    if user_update.is_active is not None:
        current_user.is_active = user_update.is_active
    if getattr(user_update, 'avatar_url', None) is not None:
        current_user.avatar_url = user_update.avatar_url
    current_user.updated_at = datetime.now()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get('/api/users/{user_id}', response_model=UserResponse)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    return user_obj

@app.get('/api/users', response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    users = db.query(User).all()
    return users




