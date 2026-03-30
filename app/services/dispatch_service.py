from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.car import Car
from app.models.car_task_assignment import CarTaskAssignment
from app.models.enums import (
    AppointmentStatus,
    CarTaskStatus,
    ExpressStatus,
    GeocodingStatus,
    TaskStatus,
    UserRole,
)
from app.models.express import Express
from app.models.task import Task
from app.models.user import User
from app.services.car_ws_manager import send_car_control_message
from app.services.errors import ServiceError


class DispatchService:
    """简易任务调度与“车完成回传”同步服务。"""

    def _ensure_admin(self, current_user: User) -> None:
        if current_user.role != UserRole.admin:
            raise ServiceError(status_code=403, detail="仅管理员可执行该操作")

    def _get_or_404_car(self, db: Session, car_id: int) -> Car:
        item = db.query(Car).filter(Car.id == car_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="小车不存在")
        return item

    def _get_task_or_404(self, db: Session, task_id: int) -> Task:
        item = db.query(Task).filter(Task.id == task_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="任务不存在")
        return item

    async def run_dispatch_cycle(self, db: Session, current_user: User) -> Dict[str, Any]:
        """执行一次调度周期：A(建任务) -> B(分配)。

        任务完成由小车通过 WebSocket 回传触发；因此这里不做“同步 completed”轮询。
        """
        self._ensure_admin(current_user)

        started_at = datetime.utcnow()
        created_task_ids: List[int] = []
        assigned_task_ids: List[int] = []
        dispatched_messages = 0
        assignment_contexts: List[Dict[str, Any]] = []

        # Step A：为 scheduled 预约创建 pending Task（当且仅当 Express 未绑定 Task）
        scheduled_rows = (
            db.query(Appointment, Express)
            .join(Express, Appointment.express_id == Express.id)
            .filter(Appointment.status == AppointmentStatus.scheduled)
            .filter(Express.task_id.is_(None))
            .all()
        )

        for appointment, express in scheduled_rows:
            new_task = Task(
                status=TaskStatus.pending,
                car_id=None,
                user_id=appointment.customer_id,
                target_address=appointment.pickup_address,
                target_latitude=None,
                target_longitude=None,
                coord_system="WGS84",
                geocoder_place_id=None,
                geocoder_accuracy_m=None,
                geocoding_status=GeocodingStatus.pending,
                geocoded_at=None,
                expected_completion_time=appointment.appointment_time,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(new_task)
            db.flush()  # 生成 task.id（尚未提交事务）

            express.task_id = new_task.id
            created_task_ids.append(new_task.id)

        # 由于 SessionLocal 配置了 autoflush=False，Step B 之前显式 flush 一次，
        # 确保 Express.task_id 的更新对后续查询可见。
        db.flush()

        # Step B：为 idle 小车分配 pending 任务（只处理一辆车/一个任务即可满足当前验收）
        car = (
            db.query(Car)
            .filter(Car.is_active.is_(True))
            .filter(Car.task_status == CarTaskStatus.idle)
            .order_by(Car.id.asc())
            .first()
        )

        if car:
            task_row = (
                db.query(Task, Express, Appointment)
                .join(Express, Express.task_id == Task.id)
                .join(Appointment, Appointment.express_id == Express.id)
                .filter(Task.status == TaskStatus.pending)
                .filter(Task.car_id.is_(None))
                .filter(Express.status == ExpressStatus.unassigned)
                .filter(Appointment.status == AppointmentStatus.scheduled)
                .order_by(Appointment.appointment_time.asc(), Task.created_at.asc())
                .first()
            )

            if task_row:
                task, express, appointment = task_row

                task.status = TaskStatus.running
                task.car_id = car.id
                task.updated_at = datetime.now()

                car.task_status = CarTaskStatus.delivering
                car.current_task_id = task.id
                car.updated_at = datetime.now()

                express.status = ExpressStatus.delivering
                express.updated_at = datetime.now()

                db.add(
                    CarTaskAssignment(
                        car_id=car.id,
                        task_id=task.id,
                        status=CarTaskStatus.delivering,
                        assigned_at=datetime.now(),
                        unassigned_at=None,
                    )
                )

                assigned_task_ids.append(task.id)
                assignment_contexts.append(
                    {
                        "car_id": car.id,
                        "task_id": task.id,
                        "express_id": express.id,
                        "appointment_id": appointment.id,
                        "target_address": task.target_address,
                        "target_latitude": float(task.target_latitude) if task.target_latitude is not None else None,
                        "target_longitude": float(task.target_longitude) if task.target_longitude is not None else None,
                        "coord_system": task.coord_system,
                        "expected_completion_time": appointment.appointment_time.isoformat()
                        if appointment.appointment_time
                        else None,
                    }
                )

        db.commit()

        # 发送下发指令（若小车尚未连接，则允许本次周期跳过；下一次分配/重连后可继续补发）
        for ctx in assignment_contexts:
            payload = {
                "type": "dispatch_task",
                "task_id": ctx["task_id"],
                "express_id": ctx["express_id"],
                "appointment_id": ctx["appointment_id"],
                # 预留给你后续“要传给小车的其他信息”
                "reserved": {},
                "target": {
                    "address": ctx["target_address"],
                    "latitude": ctx["target_latitude"],
                    "longitude": ctx["target_longitude"],
                    "coord_system": ctx["coord_system"],
                },
                "expected_completion_time": ctx["expected_completion_time"],
            }
            if await send_car_control_message(ctx["car_id"], payload):
                dispatched_messages += 1

        # 返回一个普通 dict，Controller 可映射到 response_model
        return {
            "started_at": started_at,
            "created_task_ids": created_task_ids,
            "assigned_task_ids": assigned_task_ids,
            "dispatched_messages": dispatched_messages,
            "skipped": None,
        }

    async def mark_task_completed_from_car(
        self,
        db: Session,
        *,
        car_id: int,
        task_id: int,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """接收小车 `task_completed` 回传并同步 completed。

        幂等策略：
        - 若 Task 已 completed，则直接返回。
        - 若 Task 未绑定该 car_id，则拒绝/忽略（防止串车回传）。
        """
        car = self._get_or_404_car(db, car_id)
        task = self._get_task_or_404(db, task_id)

        if task.status == TaskStatus.completed:
            return

        if task.car_id != car.id:
            raise ServiceError(status_code=409, detail="任务与小车不匹配，无法完成同步")

        # 找到 Express（Task 与 Express 关系是一对一/或由 Express.task_id 反查）
        express = db.query(Express).filter(Express.task_id == task.id).first()
        if not express:
            raise ServiceError(status_code=404, detail="任务对应快递不存在")

        appointment = db.query(Appointment).filter(Appointment.express_id == express.id).first()

        now = datetime.now()

        task.status = TaskStatus.completed
        task.completed_at = now
        task.updated_at = now

        express.status = ExpressStatus.completed
        express.updated_at = now

        if appointment:
            appointment.status = AppointmentStatus.delivered
            appointment.updated_at = now

        # 恢复小车为空闲
        car.task_status = CarTaskStatus.idle
        car.current_task_id = None
        car.updated_at = now

        # 可选：更新分配记录（若存在未结束的记录）
        assignment = (
            db.query(CarTaskAssignment)
            .filter(CarTaskAssignment.car_id == car.id)
            .filter(CarTaskAssignment.task_id == task.id)
            .filter(CarTaskAssignment.unassigned_at.is_(None))
            .first()
        )
        if assignment:
            assignment.unassigned_at = now
            assignment.status = CarTaskStatus.idle
            assignment.updated_at = now

        db.commit()

