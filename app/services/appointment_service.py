from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.enums import UserRole
from app.models.express import Express
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentStatusUpdate,
    AppointmentUpdate,
)
from app.services.errors import ServiceError


class AppointmentService:
    """预约相关业务服务。"""

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def _ensure_access(self, appointment: Appointment, current_user: User) -> None:
        """确保当前用户可访问指定预约。"""
        if current_user.role != UserRole.admin and appointment.customer_id != current_user.id:
            raise ServiceError(status_code=403, detail="无权限访问该预约")

    def _get_or_404(self, db: Session, appointment_id: int) -> Appointment:
        """获取预约，不存在则抛出 404。"""
        item = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="预约不存在")
        return item

    def _get_express_by_tracking_or_400(self, db: Session, tracking_number: str) -> Express:
        """按快递单号获取快递，不存在则抛出 400。"""
        express = db.query(Express).filter(Express.tracking_number == tracking_number).first()
        if not express:
            raise ServiceError(status_code=400, detail="快递单号不存在")
        return express

    def create_appointment(self, db: Session, current_user: User, payload: AppointmentCreate) -> Appointment:
        """创建预约。"""
        if current_user.role != UserRole.admin and payload.customer_id != current_user.id:
            raise ServiceError(status_code=403, detail="只能为自己创建预约")

        express = self._get_express_by_tracking_or_400(db, payload.express_tracking_number)

        new_item = Appointment(
            customer_id=payload.customer_id,
            express_id=express.id,
            pickup_address=payload.pickup_address,
            appointment_time=payload.appointment_time,
            status=payload.status,
            notes=payload.notes,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(new_item)
        self._commit(db)
        db.refresh(new_item)
        return new_item

    def get_appointment(self, db: Session, current_user: User, appointment_id: int) -> Appointment:
        """获取预约详情。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)
        return item

    def list_appointments(self, db: Session, current_user: User) -> List[Appointment]:
        """列出预约列表。"""
        if current_user.role == UserRole.admin:
            return db.query(Appointment).all()
        return db.query(Appointment).filter(Appointment.customer_id == current_user.id).all()

    def update_appointment(self, db: Session, current_user: User, appointment_id: int, payload: AppointmentUpdate) -> Appointment:
        """更新预约字段。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)

        if payload.appointment_time is not None:
            item.appointment_time = payload.appointment_time
        if payload.status is not None:
            item.status = payload.status
        if payload.pickup_address is not None:
            item.pickup_address = payload.pickup_address
        if payload.notes is not None:
            item.notes = payload.notes

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def update_appointment_status(self, db: Session, current_user: User, appointment_id: int, payload: AppointmentStatusUpdate) -> Appointment:
        """更新预约状态。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)

        item.status = payload.status
        if payload.notes is not None:
            item.notes = payload.notes
        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def reschedule_appointment(self, db: Session, current_user: User, appointment_id: int, payload: AppointmentReschedule) -> Appointment:
        """重新安排预约时间。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)

        item.appointment_time = payload.appointment_time
        if payload.notes is not None:
            item.notes = payload.notes
        item.updated_at = datetime.now()

        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

