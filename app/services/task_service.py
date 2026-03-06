from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.car import Car
from app.models.enums import UserRole
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskStatusUpdate, TaskUpdate
from app.services.errors import ServiceError


class TaskService:
    """任务相关业务服务。

    - 负责权限判断、查库写库与字段更新；
    - 通过 `ServiceError` 抛出可被 Controller 映射为 HTTPException 的错误信息。
    """

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def _ensure_access(self, task: Task, current_user: User) -> None:
        """确保当前用户可访问指定任务。"""
        if current_user.role != UserRole.admin and task.user_id != current_user.id:
            raise ServiceError(status_code=403, detail="无权限访问该任务")

    def _get_task_or_404(self, db: Session, task_id: int) -> Task:
        """获取任务，不存在则抛出 404。"""
        item = db.query(Task).filter(Task.id == task_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="任务不存在")
        return item

    def _resolve_car_id(self, db: Session, assigned_car_number: Optional[str]) -> Optional[int]:
        """将 API 的 assigned_car_number 映射为 Car.id（不存在则返回 None）。"""
        if not assigned_car_number:
            return None
        car = db.query(Car).filter(Car.car_number == assigned_car_number).first()
        if not car:
            # 这里选择显式报错，避免 silently 丢失 assigned_car_number
            raise ServiceError(status_code=400, detail="小车不存在")
        return car.id

    def create_task(self, db: Session, current_user: User, payload: TaskCreate) -> Task:
        """创建任务（默认归属当前用户）。"""
        car_id = self._resolve_car_id(db, payload.assigned_car_number)
        new_item = Task(
            status=payload.status,
            car_id=car_id,
            user_id=current_user.id,
            target_address=payload.target_address,
            target_latitude=payload.target_latitude,
            target_longitude=payload.target_longitude,
            coord_system=str(payload.coord_system),
            geocoder_place_id=payload.geocoder_place_id,
            geocoder_accuracy_m=payload.geocoder_accuracy_m,
            geocoding_status=payload.geocoding_status,
            geocoded_at=payload.geocoded_at,
            expected_completion_time=payload.expected_completion_time,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(new_item)
        self._commit(db)
        db.refresh(new_item)
        return new_item

    def get_task(self, db: Session, current_user: User, task_id: int) -> Task:
        """获取任务详情。"""
        item = self._get_task_or_404(db, task_id)
        self._ensure_access(item, current_user)
        return item

    def list_tasks(self, db: Session, current_user: User) -> List[Task]:
        """列出任务列表。"""
        if current_user.role == UserRole.admin:
            return db.query(Task).all()
        return db.query(Task).filter(Task.user_id == current_user.id).all()

    def update_task(self, db: Session, current_user: User, task_id: int, payload: TaskUpdate) -> Task:
        """更新任务字段。"""
        item = self._get_task_or_404(db, task_id)
        self._ensure_access(item, current_user)

        if payload.status is not None:
            item.status = payload.status
        if payload.assigned_car_number is not None:
            item.car_id = self._resolve_car_id(db, payload.assigned_car_number)
        if payload.expected_completion_time is not None:
            item.expected_completion_time = payload.expected_completion_time
        if payload.completed_at is not None:
            item.completed_at = payload.completed_at
        if payload.target_address is not None:
            item.target_address = payload.target_address
        if payload.target_latitude is not None:
            item.target_latitude = payload.target_latitude
        if payload.target_longitude is not None:
            item.target_longitude = payload.target_longitude
        if payload.coord_system is not None:
            item.coord_system = str(payload.coord_system)
        if payload.geocoder_place_id is not None:
            item.geocoder_place_id = payload.geocoder_place_id
        if payload.geocoder_accuracy_m is not None:
            item.geocoder_accuracy_m = payload.geocoder_accuracy_m
        if payload.geocoding_status is not None:
            item.geocoding_status = payload.geocoding_status
        if payload.geocoded_at is not None:
            item.geocoded_at = payload.geocoded_at

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def update_task_status(self, db: Session, current_user: User, task_id: int, payload: TaskStatusUpdate) -> Task:
        """仅更新任务状态（并按旧逻辑补齐完成时间）。"""
        item = self._get_task_or_404(db, task_id)
        self._ensure_access(item, current_user)

        item.status = payload.status
        if payload.completed_at is not None:
            item.completed_at = payload.completed_at
        elif str(payload.status) == "completed":
            item.completed_at = datetime.now()

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

