from fastapi import APIRouter, Request
from app.schemas.user import UserCreate, UserResponse, UserLogin
from datetime import datetime
from app.core.security import create_access_token, get_password_hash, verify_password, get_user, get_email, authenticate_user, get_current_user


from fastapi import status, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from fastapi.exceptions import HTTPException
from app.models.user import User
from app.core.security import Token
from fastapi.security import OAuth2PasswordRequestForm
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = APIRouter()

@app.post('/api/users/register', response_model = UserResponse, status_code = status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "用户已被注册")
    db_email = get_email(db, user.email)
    if db_email:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "邮箱已被注册")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username = user.username,
        email = user.email,
        name = user.name,
        phone = user.phone,
        address = user.address,
        role = user.role,
        is_active = True,
        hashed_password = hashed_password,
        created_at = datetime.now(),
        updated_at = datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post('api/users/login', response_model = Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "用户名或密码错误")
    access_token_expires = timedelta(minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(data = {"sub": user.username}, expires_delta = access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/api/users/me', response_model = UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user




