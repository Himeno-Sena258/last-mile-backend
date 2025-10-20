from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.models.express import Express
from app.schemas.express import (
    ExpressCreate,
    ExpressUpdate,
    ExpressResponse,
    ExpressStatusUpdate,
)

router = APIRouter()


def _ensure_access(express_item: Express, current_user: User):
    if current_user.role != UserRole.admin and express_item.recipient_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该快递")


@router.post('/api/express', response_model=ExpressResponse, status_code=status.HTTP_201_CREATED)
async def create_express(payload: ExpressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 普通用户仅能为自己创建
    if current_user.role != UserRole.admin and payload.recipient_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能为自己创建快递")

    # 快递单号唯一性校验
    exists = db.query(Express).filter(Express.tracking_number == payload.tracking_number).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="快递单号已存在")

    new_item = Express(
        recipient_name=payload.recipient_name,
        recipient_phone=payload.recipient_phone,
        recipient_address=payload.recipient_address,
        tracking_number=payload.tracking_number,
        recipient_user_id=payload.recipient_user_id,
        status=payload.status,
        station_name=payload.station_name,
        station_address=payload.station_address,
        task_id=payload.task_id,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get('/api/express/{express_id}', response_model=ExpressResponse)
async def get_express(express_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Express).filter(Express.id == express_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="快递不存在")
    _ensure_access(item, current_user)
    return item


@router.get('/api/express', response_model=List[ExpressResponse])
async def list_express(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.admin:
        items = db.query(Express).all()
    else:
        items = db.query(Express).filter(Express.recipient_user_id == current_user.id).all()
    return items


@router.put('/api/express/{express_id}', response_model=ExpressResponse)
async def update_express(express_id: int, payload: ExpressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Express).filter(Express.id == express_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="快递不存在")
    _ensure_access(item, current_user)

    if payload.recipient_name is not None:
        item.recipient_name = payload.recipient_name
    if payload.recipient_phone is not None:
        item.recipient_phone = payload.recipient_phone
    if payload.recipient_address is not None:
        item.recipient_address = payload.recipient_address
    if payload.status is not None:
        item.status = payload.status
    if payload.station_name is not None:
        item.station_name = payload.station_name
    if payload.station_address is not None:
        item.station_address = payload.station_address
    if payload.task_id is not None:
        item.task_id = payload.task_id

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch('/api/express/{express_id}/status', response_model=ExpressResponse)
async def update_express_status(express_id: int, payload: ExpressStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Express).filter(Express.id == express_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="快递不存在")
    _ensure_access(item, current_user)

    item.status = payload.status
    if payload.station_name is not None:
        item.station_name = payload.station_name
    if payload.station_address is not None:
        item.station_address = payload.station_address

    db.add(item)
    db.commit()
    db.refresh(item)
    return item