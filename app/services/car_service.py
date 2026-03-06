from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.car import Car
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.car import CarCreate, CarLocationUpdate, CarStatusUpdate, CarUpdate
from app.services.errors import ServiceError


class CarService:
    """小车相关业务服务（HTTP 接口部分）。"""

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def _ensure_admin(self, current_user: User) -> None:
        """确保当前用户为管理员。"""
        if current_user.role != UserRole.admin:
            raise ServiceError(status_code=403, detail="仅管理员可执行该操作")

    def _get_or_404(self, db: Session, car_id: int) -> Car:
        """获取小车，不存在则抛出 404。"""
        item = db.query(Car).filter(Car.id == car_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="小车不存在")
        return item

    def create_car(self, db: Session, current_user: User, payload: CarCreate) -> Car:
        """创建小车。"""
        self._ensure_admin(current_user)

        exists = db.query(Car).filter(Car.car_number == payload.car_number).first()
        if exists:
            raise ServiceError(status_code=400, detail="小车编号已存在")

        new_item = Car(
            car_number=payload.car_number,
            task_status=payload.task_status,
            current_speed=payload.current_speed,
            current_latitude=payload.current_latitude,
            current_longitude=payload.current_longitude,
            battery_level=payload.battery_level,
            running_time=payload.running_time,
            is_active=payload.is_active,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(new_item)
        self._commit(db)
        db.refresh(new_item)
        return new_item

    def get_car(self, db: Session, current_user: User, car_id: int) -> Car:
        """获取小车详情。"""
        self._ensure_admin(current_user)
        return self._get_or_404(db, car_id)

    def list_cars(self, db: Session, current_user: User) -> List[Car]:
        """列出小车列表。"""
        self._ensure_admin(current_user)
        return db.query(Car).all()

    def update_car(self, db: Session, current_user: User, car_id: int, payload: CarUpdate) -> Car:
        """更新小车字段。"""
        self._ensure_admin(current_user)
        item = self._get_or_404(db, car_id)

        if payload.car_number is not None:
            exists = db.query(Car).filter(Car.car_number == payload.car_number, Car.id != car_id).first()
            if exists:
                raise ServiceError(status_code=400, detail="小车编号已存在")
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

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def update_car_location(self, db: Session, current_user: User, car_id: int, payload: CarLocationUpdate) -> Car:
        """更新小车位置。"""
        self._ensure_admin(current_user)
        item = self._get_or_404(db, car_id)

        item.current_latitude = payload.current_latitude
        item.current_longitude = payload.current_longitude
        if payload.current_speed is not None:
            item.current_speed = payload.current_speed

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def update_car_status(self, db: Session, current_user: User, car_id: int, payload: CarStatusUpdate) -> Car:
        """更新小车状态。"""
        self._ensure_admin(current_user)
        item = self._get_or_404(db, car_id)

        item.task_status = payload.task_status
        item.current_task_id = payload.current_task_id
        if payload.battery_level is not None:
            item.battery_level = payload.battery_level
        if payload.running_time is not None:
            item.running_time = payload.running_time

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

