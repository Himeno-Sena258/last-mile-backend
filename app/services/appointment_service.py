from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, ExpressStatus, GeocodingStatus, TaskStatus
from app.models.task import Task
from app.models.express import Express
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentStatusUpdate,
    AppointmentUpdate,
)
from app.services.errors import ServiceError
from app.core.permissions import Permission, has_permission, require_permission, require_owner


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
        require_owner(current_user, Permission.APPOINTMENT, Permission.APPOINTMENT_ALL, appointment.customer_id)

    def _ensure_status(self, current_user: User, status) -> None:
        if status is not None and not has_permission(current_user, Permission.APPOINTMENT_ALL) and status not in (
            AppointmentStatus.scheduled, AppointmentStatus.cancelled
        ):
            raise ServiceError(status_code=403, detail="不能直接设置配送完成状态")

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
        require_owner(current_user, Permission.APPOINTMENT, Permission.APPOINTMENT_ALL, payload.customer_id)
        self._ensure_status(current_user, payload.status)

        express = self._get_express_by_tracking_or_400(db, payload.express_tracking_number)
        express = db.query(Express).filter(Express.id == express.id).with_for_update().one()
        require_owner(current_user, Permission.APPOINTMENT, Permission.APPOINTMENT_ALL, express.recipient_user_id)
        if express.status != ExpressStatus.unassigned or express.task_id is not None:
            raise ServiceError(status_code=409, detail="快递已进入配送流程")
        if db.query(Appointment).filter(
            Appointment.express_id == express.id,
            Appointment.status == AppointmentStatus.scheduled,
        ).first():
            raise ServiceError(status_code=409, detail="该快递已有有效预约")

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

    def _sync_pending_task(self, db: Session, item: Appointment) -> None:
        express = db.query(Express).filter(Express.id == item.express_id).with_for_update().one()
        if express.task_id is None:
            return
        task = db.query(Task).filter(Task.id == express.task_id).with_for_update().one()
        if task.status != TaskStatus.pending:
            raise ServiceError(status_code=409, detail="配送已开始，无法修改预约")
        if item.status != AppointmentStatus.scheduled:
            task.status = TaskStatus.cancelled
            express.task_id = None
        else:
            if task.target_address != item.pickup_address:
                task.target_latitude = None
                task.target_longitude = None
                task.geocoding_status = GeocodingStatus.pending
                task.geocoded_at = None
                task.geocoder_place_id = None
                task.geocoder_accuracy_m = None
            task.target_address = item.pickup_address
            task.expected_completion_time = item.appointment_time
        task.updated_at = datetime.now()

    def get_appointment(self, db: Session, current_user: User, appointment_id: int) -> Appointment:
        """获取预约详情。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)
        return item

    def list_appointments(self, db: Session, current_user: User) -> List[Appointment]:
        """列出预约列表。"""
        require_permission(current_user, Permission.APPOINTMENT)
        if has_permission(current_user, Permission.APPOINTMENT_ALL):
            return db.query(Appointment).all()
        return db.query(Appointment).filter(Appointment.customer_id == current_user.id).all()

    def update_appointment(self, db: Session, current_user: User, appointment_id: int, payload: AppointmentUpdate) -> Appointment:
        """更新预约字段。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)
        self._ensure_status(current_user, payload.status)

        if payload.appointment_time is not None:
            item.appointment_time = payload.appointment_time
        if payload.status is not None:
            item.status = payload.status
        if payload.pickup_address is not None:
            item.pickup_address = payload.pickup_address
        if payload.notes is not None:
            item.notes = payload.notes

        item.updated_at = datetime.now()
        self._sync_pending_task(db, item)
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def update_appointment_status(self, db: Session, current_user: User, appointment_id: int, payload: AppointmentStatusUpdate) -> Appointment:
        """更新预约状态。"""
        item = self._get_or_404(db, appointment_id)
        self._ensure_access(item, current_user)
        self._ensure_status(current_user, payload.status)

        item.status = payload.status
        if payload.notes is not None:
            item.notes = payload.notes
        item.updated_at = datetime.now()
        self._sync_pending_task(db, item)
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
        self._sync_pending_task(db, item)
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

