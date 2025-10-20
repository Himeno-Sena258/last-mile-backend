from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.models.appointment import Appointment
from app.models.express import Express
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    AppointmentReschedule,
)

router = APIRouter()


def _ensure_access(appointment: Appointment, current_user: User):
    if current_user.role != UserRole.admin and appointment.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该预约")


@router.post('/api/appointments', response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin and payload.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能为自己创建预约")

    # 验证快递单号存在
    express = db.query(Express).filter(Express.tracking_number == payload.express_tracking_number).first()
    if not express:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="快递单号不存在")

    new_item = Appointment(
        customer_id=payload.customer_id,
        express_tracking_number=payload.express_tracking_number,
        appointment_time=payload.appointment_time,
        status=payload.status,
        notes=payload.notes,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get('/api/appointments/{appointment_id}', response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    _ensure_access(item, current_user)
    return item


@router.get('/api/appointments', response_model=List[AppointmentResponse])
async def list_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.admin:
        items = db.query(Appointment).all()
    else:
        items = db.query(Appointment).filter(Appointment.customer_id == current_user.id).all()
    return items


@router.put('/api/appointments/{appointment_id}', response_model=AppointmentResponse)
async def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    _ensure_access(item, current_user)

    if payload.appointment_time is not None:
        item.appointment_time = payload.appointment_time
    if payload.status is not None:
        item.status = payload.status
    if payload.notes is not None:
        item.notes = payload.notes

    item.updated_at = datetime.now()
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch('/api/appointments/{appointment_id}/status', response_model=AppointmentResponse)
async def update_appointment_status(appointment_id: int, payload: AppointmentStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    _ensure_access(item, current_user)

    item.status = payload.status
    if payload.notes is not None:
        item.notes = payload.notes
    item.updated_at = datetime.now()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch('/api/appointments/{appointment_id}/reschedule', response_model=AppointmentResponse)
async def reschedule_appointment(appointment_id: int, payload: AppointmentReschedule, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    _ensure_access(item, current_user)

    item.appointment_time = payload.appointment_time
    if payload.notes is not None:
        item.notes = payload.notes
    item.updated_at = datetime.now()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item