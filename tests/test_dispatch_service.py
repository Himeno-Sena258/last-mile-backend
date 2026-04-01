from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.car import Car
from app.models.car_task_assignment import CarTaskAssignment
from app.models.enums import (
    AppointmentStatus,
    CarTaskStatus,
    ExpressStatus,
    TaskStatus,
    UserRole,
    GeocodingStatus,
)
from app.models.express import Express
from app.models.task import Task
from app.models.user import User
from app.models.user_address import Address
from app.services.dispatch_service import DispatchService
from app.services.errors import ServiceError


def _create_basic_user(db: Session) -> User:
    u = User(
        username="admin1",
        email="admin1@example.com",
        hashed_password="hash",
        name="Admin",
        phone=None,
        role=UserRole.admin,
        is_active=True,
        avatar_url=None,
    )
    db.add(u)
    db.flush()
    return u


def _create_recipient_user(db: Session) -> User:
    u = User(
        username="customer1",
        email="customer1@example.com",
        hashed_password="hash",
        name="Customer",
        phone=None,
        role=UserRole.customer,
        is_active=True,
        avatar_url=None,
    )
    db.add(u)
    db.flush()
    return u


def _create_car(db: Session, *, car_number: str = "CAR-001") -> Car:
    car = Car(
        car_number=car_number,
        task_status=CarTaskStatus.idle,
        current_task_id=None,
        current_speed=0.0,
        current_latitude=None,
        current_longitude=None,
        battery_level=100.0,
        running_time=0,
        is_active=True,
    )
    db.add(car)
    db.flush()
    return car


def _create_address(db: Session, text: str) -> Address:
    addr = Address(address_text=text, latitude=None, longitude=None, coord_system="WGS84")
    db.add(addr)
    db.flush()
    return addr


def _create_express_and_appointment(db: Session, *, recipient: User, customer: User):
    addr = _create_address(db, "Test recipient address")
    express = Express(
        recipient_name="Tom",
        recipient_phone="13800000000",
        recipient_address_id=addr.id,
        tracking_number="TRACK-001",
        pickup_code=None,
        recipient_user_id=recipient.id,
        status=ExpressStatus.unassigned,
        task_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(express)
    db.flush()

    appointment = Appointment(
        customer_id=customer.id,
        express_id=express.id,
        pickup_address="Pickup A",
        appointment_time=datetime.now(),
        status=AppointmentStatus.scheduled,
        notes=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(appointment)
    db.flush()
    return express, appointment


@pytest.mark.asyncio
async def test_dispatch_cycle_creates_task_assigns_car_and_sends_message(db_session: Session, monkeypatch):
    db: Session = db_session
    admin = _create_basic_user(db)
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)

    sent_payloads = []

    async def fake_send_car_control_message(car_id: int, payload: dict) -> bool:
        sent_payloads.append((car_id, payload))
        return True

    service = DispatchService()
    # DispatchService 在模块 import 时已绑定 send_car_control_message，所以要 monkeypatch 到 dispatch_service 模块作用域
    monkeypatch.setattr("app.services.dispatch_service.send_car_control_message", fake_send_car_control_message)

    result = await service.run_dispatch_cycle(db=db, current_user=admin)

    # Step A：创建了 Task，并绑定到 Express
    express_db = db.query(Express).filter(Express.id == express.id).first()
    assert express_db.task_id is not None
    task_id = express_db.task_id

    task_db = db.query(Task).filter(Task.id == task_id).first()
    assert task_db is not None
    assert task_db.status == TaskStatus.running
    assert task_db.car_id == car.id
    assert task_db.target_address == appointment.pickup_address
    assert task_db.geocoding_status == GeocodingStatus.pending

    # Step B：小车与 Express 状态同步
    car_db = db.query(Car).filter(Car.id == car.id).first()
    assert car_db.task_status == CarTaskStatus.delivering
    assert car_db.current_task_id == task_db.id

    express_db = db.query(Express).filter(Express.id == express.id).first()
    assert express_db.status == ExpressStatus.delivering

    assignment = db.query(CarTaskAssignment).filter(CarTaskAssignment.car_id == car.id).filter(CarTaskAssignment.task_id == task_db.id).first()
    assert assignment is not None
    assert assignment.status == CarTaskStatus.delivering

    # 消息下发
    assert len(sent_payloads) == 1
    sent_car_id, payload = sent_payloads[0]
    assert sent_car_id == car.id
    assert payload["type"] == "dispatch_task"
    assert payload["task_id"] == task_db.id
    assert result["assigned_task_ids"] == [task_db.id]


@pytest.mark.asyncio
async def test_mark_task_completed_from_car_updates_completed_states(db_session: Session):
    db: Session = db_session
    admin = _create_basic_user(db)
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)

    # 直接创建一个 pending/running 的任务并绑定，模拟“已分配但尚未完成”
    task = Task(
        status=TaskStatus.running,
        car_id=car.id,
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
        completed_at=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(task)
    db.flush()
    express.task_id = task.id
    express.status = ExpressStatus.delivering
    appointment.status = AppointmentStatus.scheduled

    car.task_status = CarTaskStatus.delivering
    car.current_task_id = task.id

    assignment = CarTaskAssignment(
        car_id=car.id,
        task_id=task.id,
        assigned_at=datetime.now(),
        unassigned_at=None,
        status=CarTaskStatus.delivering,
    )
    db.add(assignment)
    db.commit()

    service = DispatchService()
    await service.mark_task_completed_from_car(db, car_id=car.id, task_id=task.id)

    task_db = db.query(Task).filter(Task.id == task.id).first()
    assert task_db.status == TaskStatus.completed
    assert task_db.completed_at is not None

    express_db = db.query(Express).filter(Express.id == express.id).first()
    assert express_db.status == ExpressStatus.completed

    appointment_db = db.query(Appointment).filter(Appointment.id == appointment.id).first()
    assert appointment_db.status == AppointmentStatus.delivered

    car_db = db.query(Car).filter(Car.id == car.id).first()
    assert car_db.task_status == CarTaskStatus.idle
    assert car_db.current_task_id is None

    assignment_db = db.query(CarTaskAssignment).filter(CarTaskAssignment.car_id == car.id).filter(CarTaskAssignment.task_id == task.id).first()
    assert assignment_db.unassigned_at is not None
    assert assignment_db.status == CarTaskStatus.idle


@pytest.mark.asyncio
async def test_mark_task_completed_from_car_idempotent(db_session: Session):
    db: Session = db_session
    admin = _create_basic_user(db)
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)

    task = Task(
        status=TaskStatus.running,
        car_id=car.id,
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
        completed_at=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(task)
    db.flush()
    express.task_id = task.id
    express.status = ExpressStatus.delivering
    appointment.status = AppointmentStatus.scheduled
    car.task_status = CarTaskStatus.delivering
    car.current_task_id = task.id
    db.add(
        CarTaskAssignment(
            car_id=car.id,
            task_id=task.id,
            assigned_at=datetime.now(),
            unassigned_at=None,
            status=CarTaskStatus.delivering,
        )
    )
    db.commit()

    service = DispatchService()
    await service.mark_task_completed_from_car(db, car_id=car.id, task_id=task.id)
    task_db_1 = db.query(Task).filter(Task.id == task.id).first()

    await service.mark_task_completed_from_car(db, car_id=car.id, task_id=task.id)
    task_db_2 = db.query(Task).filter(Task.id == task.id).first()

    assert task_db_2.status == TaskStatus.completed
    assert task_db_2.completed_at == task_db_1.completed_at


@pytest.mark.asyncio
async def test_mark_task_completed_from_car_mismatched_car_raises(db_session: Session):
    db: Session = db_session
    admin = _create_basic_user(db)
    customer = _create_recipient_user(db)
    car1 = _create_car(db, car_number="CAR-001")
    car2 = _create_car(db, car_number="CAR-002")
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)

    task = Task(
        status=TaskStatus.running,
        car_id=car1.id,
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
        completed_at=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(task)
    db.flush()
    express.task_id = task.id
    express.status = ExpressStatus.delivering
    car1.task_status = CarTaskStatus.delivering
    car1.current_task_id = task.id
    db.add(
        CarTaskAssignment(
            car_id=car1.id,
            task_id=task.id,
            assigned_at=datetime.now(),
            unassigned_at=None,
            status=CarTaskStatus.delivering,
        )
    )
    db.commit()

    service = DispatchService()
    with pytest.raises(ServiceError) as excinfo:
        await service.mark_task_completed_from_car(db, car_id=car2.id, task_id=task.id)
    assert excinfo.value.status_code == 409

