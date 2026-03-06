from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from dotenv import load_dotenv

from app.core.security import Token, get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api._helpers import raise_http
from app.services.errors import ServiceError
from app.services.user_service import UserService

load_dotenv()

app = APIRouter()
_user_service = UserService()


@app.post('/api/users/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """注册用户（协议保持不变）。"""
    try:
        return _user_service.register_user(db=db, payload=user)
    except ServiceError as e:
        raise_http(e)


@app.post('/api/users/login', response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录并返回 JWT（协议保持不变）。"""
    try:
        return _user_service.login_user(db=db, username=form_data.username, password=form_data.password)
    except ServiceError as e:
        raise_http(e)


@app.get('/api/users/me', response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息（协议保持不变）。"""
    return current_user


@app.put('/api/users/me', response_model=UserResponse)
async def update_current_user(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新当前用户信息（协议保持不变）。"""
    try:
        return _user_service.update_current_user(db=db, current_user=current_user, payload=user_update)
    except ServiceError as e:
        raise_http(e)


@app.get('/api/users/{user_id}', response_model=UserResponse)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """按 ID 获取用户（协议保持不变）。"""
    try:
        return _user_service.get_user_by_id(db=db, current_user=current_user, user_id=user_id)
    except ServiceError as e:
        raise_http(e)


@app.get('/api/users', response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出全部用户（协议保持不变）。"""
    try:
        return _user_service.list_users(db=db, current_user=current_user)
    except ServiceError as e:
        raise_http(e)




