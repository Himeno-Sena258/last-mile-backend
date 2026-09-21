from __future__ import annotations

from datetime import datetime, timedelta
import uuid
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
)
from app.models.express import Express
from app.models.task import Task
from app.models.dispatch_command import DispatchCommand
from app.models.user import User
from app.services.car_ws_manager import get_car_control_connection, send_car_control_message
from app.services.errors import ServiceError
from app.core.permissions import Permission, require_permission


class DispatchService:
    """简易任务调度与“车完成回传”同步服务。"""

    def _ensure_admin(self, current_user: User) -> None:
        require_permission(current_user, Permission.DISPATCH)

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

    def mark_car_connected(self, db: Session, car_id: int) -> None:
        car = self._get_or_404_car(db, car_id)
        now = datetime.now()
        car.connected_at = now
        car.last_seen_at = now
        if car.current_task_id is None:
            car.task_status = CarTaskStatus.idle
        db.commit()

    def mark_car_seen(self, db: Session, car_id: int) -> None:
        car = self._get_or_404_car(db, car_id)
        car.last_seen_at = datetime.now()
        db.commit()

    def mark_cars_offline(self, db: Session, car_ids: List[int]) -> None:
        if not car_ids:
            return
        cars = db.query(Car).filter(Car.id.in_(car_ids)).all()
        for car in cars:
            car.task_status = CarTaskStatus.offline
        db.commit()

    def reconcile_running_interruptions(self, db: Session) -> int:
        """Mark running work interrupted only after the reconnect grace period."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=30)
        commands = (
            db.query(DispatchCommand)
            .join(Car, Car.id == DispatchCommand.car_id)
            .filter(DispatchCommand.status == "accepted")
            .filter(Car.task_status == CarTaskStatus.offline)
            .filter((Car.last_seen_at.is_(None)) | (Car.last_seen_at < cutoff))
            .all()
        )
        for command in commands:
            command.status = "interrupted"
            command.interrupted_at = now
            assignment = db.query(CarTaskAssignment).filter(
                CarTaskAssignment.car_id == command.car_id,
                CarTaskAssignment.task_id == command.task_id,
                CarTaskAssignment.unassigned_at.is_(None),
            ).first()
            if assignment:
                assignment.status = CarTaskStatus.offline
        db.commit()
        return len(commands)

    def _command_payload(self, db: Session, command: DispatchCommand, *, resume: bool = False):
        row = (
            db.query(Task, Express, Appointment)
            .join(Express, Express.task_id == Task.id)
            .join(Appointment, Appointment.express_id == Express.id)
            .filter(Task.id == command.task_id)
            .first()
        )
        if not row:
            return None
        task, express, appointment = row
        return {
            "type": "dispatch_task",
            "command_id": command.command_id,
            "task_id": task.id,
            "express_id": express.id,
            "appointment_id": appointment.id,
            "resume": resume,
            "reserved": {},
            "target": {
                "address": task.target_address,
                "latitude": float(task.target_latitude) if task.target_latitude is not None else None,
                "longitude": float(task.target_longitude) if task.target_longitude is not None else None,
                "coord_system": task.coord_system,
            },
            "expected_completion_time": task.expected_completion_time.isoformat()
            if task.expected_completion_time else None,
        }

    def _release_unaccepted_command(self, db: Session, command: DispatchCommand, reason: str) -> None:
        now = datetime.now()
        task = db.get(Task, command.task_id)
        car = db.get(Car, command.car_id)
        express = db.query(Express).filter(Express.task_id == command.task_id).first()
        if task and task.status == TaskStatus.pending:
            task.car_id = None
        if express and express.status == ExpressStatus.unassigned:
            express.updated_at = now
        if car and car.current_task_id == command.task_id:
            car.current_task_id = None
            if car.task_status != CarTaskStatus.offline:
                car.task_status = CarTaskStatus.idle
        assignment = db.query(CarTaskAssignment).filter(
            CarTaskAssignment.car_id == command.car_id,
            CarTaskAssignment.task_id == command.task_id,
            CarTaskAssignment.unassigned_at.is_(None),
        ).first()
        if assignment:
            assignment.unassigned_at = now
            assignment.status = CarTaskStatus.idle
        command.status = "failed"
        command.failed_at = now
        command.failure_reason = reason

    async def process_dispatch_commands(self, db: Session) -> int:
        """Retry unacknowledged commands and release reservations after timeout."""
        # Database server defaults (CURRENT_TIMESTAMP) are UTC in SQLite and
        # PostgreSQL, so command retry timestamps use the same clock.
        now = datetime.utcnow()
        sent = 0
        commands = db.query(DispatchCommand).filter(DispatchCommand.status == "pending").with_for_update(skip_locked=True).all()
        for command in commands:
            age = now - (command.created_at or now)
            since_send = now - command.last_sent_at if command.last_sent_at else None
            if age >= timedelta(seconds=20) or (command.attempts >= 3 and since_send and since_send >= timedelta(seconds=5)):
                self._release_unaccepted_command(db, command, "车辆未确认派发指令")
                continue
            if command.last_sent_at and since_send < timedelta(seconds=5):
                continue
            if not await get_car_control_connection(command.car_id):
                continue
            payload = self._command_payload(db, command)
            if not payload:
                self._release_unaccepted_command(db, command, "派发关联数据不存在")
                continue
            command.attempts += 1
            command.last_sent_at = now
            if await send_car_control_message(command.car_id, payload):
                sent += 1
            else:
                command.failure_reason = "车辆连接不可用"
        db.commit()
        return sent

    def mark_task_accepted_from_car(self, db: Session, *, car_id: int, task_id: int, command_id: str) -> None:
        command = db.query(DispatchCommand).filter(DispatchCommand.command_id == command_id).with_for_update().first()
        if not command or command.car_id != car_id or command.task_id != task_id:
            raise ServiceError(status_code=409, detail="派发指令与车辆或任务不匹配")
        task = self._get_task_or_404(db, task_id)
        car = self._get_or_404_car(db, car_id)
        if car.current_task_id != task.id or task.car_id != car.id:
            raise ServiceError(status_code=409, detail="任务已不再分配给该车辆")
        if command.status not in ("pending", "accepted", "interrupted"):
            raise ServiceError(status_code=409, detail="派发指令已失效")
        now = datetime.now()
        command.status = "accepted"
        command.acknowledged_at = command.acknowledged_at or now
        command.interrupted_at = None
        task.status = TaskStatus.running
        task.updated_at = now
        car.task_status = CarTaskStatus.delivering
        car.last_seen_at = now
        express = db.query(Express).filter(Express.task_id == task.id).first()
        if express:
            express.status = ExpressStatus.delivering
            express.updated_at = now
        assignment = db.query(CarTaskAssignment).filter(
            CarTaskAssignment.car_id == car.id,
            CarTaskAssignment.task_id == task.id,
            CarTaskAssignment.unassigned_at.is_(None),
        ).first()
        if assignment:
            assignment.status = CarTaskStatus.delivering
        db.commit()

    async def run_dispatch_cycle(self, db: Session, current_user: User) -> Dict[str, Any]:
        """执行一次调度周期：A(建任务) -> B(分配)。

        任务完成由小车通过 WebSocket 回传触发；因此这里不做“同步 completed”轮询。
        """
        self._ensure_admin(current_user)
        return await self.dispatch_pending(db)

    async def dispatch_pending(self, db: Session) -> Dict[str, Any]:
        """Internal scheduler entry point; HTTP callers must pass the admin check."""

        started_at = datetime.utcnow()
        created_task_ids: List[int] = []
        assigned_task_ids: List[int] = []
        dispatched_messages = 0

        # Step A：为 scheduled 预约创建 pending Task（当且仅当 Express 未绑定 Task）
        scheduled_rows = (
            db.query(Appointment, Express)
            .join(Express, Appointment.express_id == Express.id)
            .filter(Appointment.status == AppointmentStatus.scheduled)
            .filter(Express.task_id.is_(None))
            .filter(Express.status == ExpressStatus.unassigned)
            .order_by(Appointment.appointment_time.asc(), Appointment.id.asc())
            .with_for_update()
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

        # Assign pending tasks in appointment order to connected idle cars.
        cars = (
            db.query(Car)
            .filter(Car.is_active.is_(True))
            .filter(Car.task_status == CarTaskStatus.idle)
            .filter(Car.current_task_id.is_(None))
            .order_by(Car.id.asc())
            .with_for_update(skip_locked=True)
            .all()
        )

        for car in cars:
            if not await get_car_control_connection(car.id):
                continue
            task_row = (
                db.query(Task, Express, Appointment)
                .join(Express, Express.task_id == Task.id)
                .join(Appointment, Appointment.express_id == Express.id)
                .filter(Task.status == TaskStatus.pending)
                .filter(Task.car_id.is_(None))
                .filter(Express.status == ExpressStatus.unassigned)
                .filter(Appointment.status == AppointmentStatus.scheduled)
                .order_by(Appointment.appointment_time.asc(), Task.created_at.asc())
                .with_for_update(skip_locked=True)
                .first()
            )

            if task_row:
                task, express, appointment = task_row

                task.car_id = car.id
                task.updated_at = datetime.now()

                # This is a reservation. Execution starts only after task_accepted.
                car.task_status = CarTaskStatus.idle
                car.current_task_id = task.id
                car.updated_at = datetime.now()

                db.add(
                    CarTaskAssignment(
                        car_id=car.id,
                        task_id=task.id,
                        status=CarTaskStatus.idle,
                        assigned_at=datetime.now(),
                        unassigned_at=None,
                    )
                )

                assigned_task_ids.append(task.id)
                command = db.query(DispatchCommand).filter(DispatchCommand.task_id == task.id).first()
                if command:
                    command.command_id = str(uuid.uuid4())
                    command.car_id = car.id
                    command.status = "pending"
                    command.attempts = 0
                    command.last_sent_at = None
                    command.acknowledged_at = None
                    command.interrupted_at = None
                    command.failed_at = None
                    command.failure_reason = None
                    command.created_at = datetime.utcnow()
                    command.updated_at = datetime.utcnow()
                else:
                    db.add(DispatchCommand(car_id=car.id, task_id=task.id, status="pending"))
                db.flush()

        db.commit()

        dispatched_messages = await self.process_dispatch_commands(db)

        # 返回一个普通 dict，Controller 可映射到 response_model
        return {
            "started_at": started_at,
            "created_task_ids": created_task_ids,
            "assigned_task_ids": assigned_task_ids,
            "dispatched_messages": dispatched_messages,
            "skipped": None,
        }

    async def resend_current_task(self, db: Session, car_id: int) -> bool:
        """Replay the same task ID on reconnect; cars must deduplicate commands by ID."""
        command = db.query(DispatchCommand).join(Task, Task.id == DispatchCommand.task_id).filter(
            DispatchCommand.car_id == car_id,
            DispatchCommand.status.in_(("pending", "accepted", "interrupted")),
            Task.car_id == car_id,
        ).first()
        if not command:
            return False
        payload = self._command_payload(db, command, resume=command.status in ("accepted", "interrupted"))
        return bool(payload and await send_car_control_message(car_id, payload))

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

        if task.car_id != car.id:
            raise ServiceError(status_code=409, detail="任务与小车不匹配，无法完成同步")

        if task.status == TaskStatus.completed:
            return
        if task.status != TaskStatus.running or car.current_task_id != task.id:
            raise ServiceError(status_code=409, detail="任务不是小车当前执行中的任务")

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

        command = db.query(DispatchCommand).filter(DispatchCommand.task_id == task.id).first()
        if command:
            command.status = "completed"
            command.interrupted_at = None

        db.commit()

