from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api._helpers import raise_http
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.appointment_service import AppointmentService
from app.services.errors import ServiceError
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    AppointmentReschedule,
)

router = APIRouter()
_appointment_service = AppointmentService()


@router.post('/api/appointments', response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建预约（协议保持不变）。"""
    try:
        return _appointment_service.create_appointment(db=db, current_user=current_user, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/appointments/{appointment_id}', response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取预约详情（协议保持不变）。"""
    try:
        return _appointment_service.get_appointment(db=db, current_user=current_user, appointment_id=appointment_id)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/appointments', response_model=List[AppointmentResponse])
async def list_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出预约列表（协议保持不变）。"""
    try:
        return _appointment_service.list_appointments(db=db, current_user=current_user)
    except ServiceError as e:
        raise_http(e)


@router.put('/api/appointments/{appointment_id}', response_model=AppointmentResponse)
async def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新预约（协议保持不变）。"""
    try:
        return _appointment_service.update_appointment(
            db=db, current_user=current_user, appointment_id=appointment_id, payload=payload
        )   
    except ServiceError as e:
        raise_http(e)


@router.patch('/api/appointments/{appointment_id}/status', response_model=AppointmentResponse)
async def update_appointment_status(appointment_id: int, payload: AppointmentStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新预约状态（协议保持不变）。"""
    try:
        return _appointment_service.update_appointment_status(
            db=db, current_user=current_user, appointment_id=appointment_id, payload=payload
        )
    except ServiceError as e:
        raise_http(e)


@router.patch('/api/appointments/{appointment_id}/reschedule', response_model=AppointmentResponse)
async def reschedule_appointment(appointment_id: int, payload: AppointmentReschedule, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """重新安排预约（协议保持不变）。"""
    try:
        return _appointment_service.reschedule_appointment(
            db=db, current_user=current_user, appointment_id=appointment_id, payload=payload
        )
    except ServiceError as e:
        raise_http(e)