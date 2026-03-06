from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api._helpers import raise_http
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.errors import ServiceError
from app.schemas.express import (
    ExpressCreate,
    ExpressUpdate,
    ExpressResponse,
    ExpressStatusUpdate,
)
from app.services.express_service import ExpressService

router = APIRouter()
_express_service = ExpressService()


@router.post('/api/express', response_model=ExpressResponse, status_code=status.HTTP_201_CREATED)
async def create_express(payload: ExpressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建快递（协议保持不变）。"""
    try:
        return _express_service.create_express(db=db, current_user=current_user, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/express/{express_id}', response_model=ExpressResponse)
async def get_express(express_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取快递详情（协议保持不变）。"""
    try:
        return _express_service.get_express(db=db, current_user=current_user, express_id=express_id)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/express', response_model=List[ExpressResponse])
async def list_express(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出快递列表（协议保持不变）。"""
    try:
        return _express_service.list_express(db=db, current_user=current_user)
    except ServiceError as e:
        raise_http(e)


@router.put('/api/express/{express_id}', response_model=ExpressResponse)
async def update_express(express_id: int, payload: ExpressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新快递（协议保持不变）。"""
    try:
        return _express_service.update_express(db=db, current_user=current_user, express_id=express_id, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.patch('/api/express/{express_id}/status', response_model=ExpressResponse)
async def update_express_status(express_id: int, payload: ExpressStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新快递状态（协议保持不变）。"""
    try:
        return _express_service.update_express_status(db=db, current_user=current_user, express_id=express_id, payload=payload)
    except ServiceError as e:
        raise_http(e)