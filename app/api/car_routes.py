from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.models.car import Car
from app.schemas.car import (
    CarCreate,
    CarUpdate,
    CarResponse,
    CarLocationUpdate,
    CarStatusUpdate,
)

router = APIRouter()


def _ensure_admin(current_user: User):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行该操作")


@router.post('/api/cars', response_model=CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(payload: CarCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)

    exists = db.query(Car).filter(Car.car_number == payload.car_number).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="小车编号已存在")

    new_item = Car(
        car_number=payload.car_number,
        task_status=payload.task_status,
        current_speed=payload.current_speed,
        current_latitude=payload.current_latitude,
        current_longitude=payload.current_longitude,
        battery_level=payload.battery_level,
        running_time=payload.running_time,
        is_active=payload.is_active,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get('/api/cars/{car_id}', response_model=CarResponse)
async def get_car(car_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    item = db.query(Car).filter(Car.id == car_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小车不存在")
    return item


@router.get('/api/cars', response_model=List[CarResponse])
async def list_cars(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    items = db.query(Car).all()
    return items


@router.put('/api/cars/{car_id}', response_model=CarResponse)
async def update_car(car_id: int, payload: CarUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    item = db.query(Car).filter(Car.id == car_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小车不存在")

    if payload.car_number is not None:
        # 唯一性校验
        exists = db.query(Car).filter(Car.car_number == payload.car_number, Car.id != car_id).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="小车编号已存在")
        item.car_number = payload.car_number
    if payload.task_status is not None:
        item.task_status = payload.task_status
    if payload.current_task_id is not None:
        item.current_task_id = payload.current_task_id
    if payload.current_speed is not None:
        item.current_speed = payload.current_speed
    if payload.current_latitude is not None:
        item.current_latitude = payload.current_latitude
    if payload.current_longitude is not None:
        item.current_longitude = payload.current_longitude
    if payload.battery_level is not None:
        item.battery_level = payload.battery_level
    if payload.running_time is not None:
        item.running_time = payload.running_time
    if payload.is_active is not None:
        item.is_active = payload.is_active

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch('/api/cars/{car_id}/location', response_model=CarResponse)
async def update_car_location(car_id: int, payload: CarLocationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    item = db.query(Car).filter(Car.id == car_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小车不存在")

    item.current_latitude = payload.current_latitude
    item.current_longitude = payload.current_longitude
    if payload.current_speed is not None:
        item.current_speed = payload.current_speed

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch('/api/cars/{car_id}/status', response_model=CarResponse)
async def update_car_status(car_id: int, payload: CarStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    item = db.query(Car).filter(Car.id == car_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小车不存在")

    item.task_status = payload.task_status
    item.current_task_id = payload.current_task_id
    if payload.battery_level is not None:
        item.battery_level = payload.battery_level
    if payload.running_time is not None:
        item.running_time = payload.running_time

    db.add(item)
    db.commit()
    db.refresh(item)
    return item