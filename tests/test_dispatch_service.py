from __future__ import annotations

from datetime import datetime, timedelta

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
from app.models.dispatch_command import DispatchCommand
from app.models.task import Task
from app.models.user import User
from app.models.user_address import Address
from app.services.dispatch_service import DispatchService
from app.services.errors import ServiceError
from app.services import car_ws_manager


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


def _create_express_and_appointment(db: Session, *, recipient: User, customer: User, tracking_number="TRACK-001"):
    addr = _create_address(db, "Test recipient address")
    express = Express(
        recipient_name="Tom",
        recipient_phone="13800000000",
        recipient_address_id=addr.id,
        tracking_number=tracking_number,
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
    async def connected(car_id):
        return object()
    monkeypatch.setattr("app.services.dispatch_service.get_car_control_connection", connected)

    result = await service.run_dispatch_cycle(db=db, current_user=admin)

    # Step A：创建了 Task，并绑定到 Express
    express_db = db.query(Express).filter(Express.id == express.id).first()
    assert express_db.task_id is not None
    task_id = express_db.task_id

    task_db = db.query(Task).filter(Task.id == task_id).first()
    assert task_db is not None
    assert task_db.status == TaskStatus.pending
    assert task_db.car_id == car.id
    assert task_db.target_address == appointment.pickup_address
    assert task_db.geocoding_status == GeocodingStatus.pending

    # Step B：小车与 Express 状态同步
    car_db = db.query(Car).filter(Car.id == car.id).first()
    assert car_db.task_status == CarTaskStatus.idle
    assert car_db.current_task_id == task_db.id

    express_db = db.query(Express).filter(Express.id == express.id).first()
    assert express_db.status == ExpressStatus.unassigned

    assignment = db.query(CarTaskAssignment).filter(CarTaskAssignment.car_id == car.id).filter(CarTaskAssignment.task_id == task_db.id).first()
    assert assignment is not None
    assert assignment.status == CarTaskStatus.idle

    # 消息下发
    assert len(sent_payloads) == 1
    sent_car_id, payload = sent_payloads[0]
    assert sent_car_id == car.id
    assert payload["type"] == "dispatch_task"
    assert payload["command_id"]
    assert payload["task_id"] == task_db.id
    assert result["assigned_task_ids"] == [task_db.id]

    service.mark_task_accepted_from_car(
        db, car_id=car.id, task_id=task_db.id, command_id=payload["command_id"]
    )
    assert task_db.status == TaskStatus.running
    assert car_db.task_status == CarTaskStatus.delivering
    assert express_db.status == ExpressStatus.delivering
    assert assignment.status == CarTaskStatus.delivering


@pytest.mark.asyncio
async def test_automatic_dispatch_waits_for_connection_and_is_idempotent(db_session, monkeypatch):
    db = db_session
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)
    service = DispatchService()
    result = await service.dispatch_pending(db)
    assert len(result["created_task_ids"]) == 1
    assert not result["assigned_task_ids"]
    assert car.current_task_id is None
    assert express.status == ExpressStatus.unassigned
    async def connected(car_id):
        return object()
    sent = []
    async def send(car_id, payload):
        sent.append(payload)
        return True
    monkeypatch.setattr("app.services.dispatch_service.get_car_control_connection", connected)
    monkeypatch.setattr("app.services.dispatch_service.send_car_control_message", send)
    await service.dispatch_pending(db)
    await service.dispatch_pending(db)
    assert db.query(Task).count() == 1
    assert db.query(CarTaskAssignment).count() == 1
    assert len(sent) == 1
    assert await service.resend_current_task(db, car.id)
    assert sent[0] == sent[1]


@pytest.mark.asyncio
async def test_dispatch_assigns_all_cars_and_continues_after_completion(db_session, monkeypatch):
    db = db_session
    customer = _create_recipient_user(db)
    cars = [_create_car(db, car_number=f"CAR-{i}") for i in range(2)]
    for i in range(3):
        _create_express_and_appointment(db, recipient=customer, customer=customer, tracking_number=f"TRACK-{i}")
    async def connected(car_id):
        return object()
    async def send(car_id, payload):
        return True
    monkeypatch.setattr("app.services.dispatch_service.get_car_control_connection", connected)
    monkeypatch.setattr("app.services.dispatch_service.send_car_control_message", send)
    service = DispatchService()
    result = await service.dispatch_pending(db)
    assert len(result["assigned_task_ids"]) == 2
    old_task_id = cars[0].current_task_id
    command = db.query(DispatchCommand).filter(DispatchCommand.task_id == old_task_id).one()
    service.mark_task_accepted_from_car(
        db, car_id=cars[0].id, task_id=old_task_id, command_id=command.command_id
    )
    await service.mark_task_completed_from_car(db, car_id=cars[0].id, task_id=old_task_id)
    next_cycle = await service.dispatch_pending(db)
    assert len(next_cycle["assigned_task_ids"]) == 1
    assert cars[0].current_task_id != old_task_id
    await service.mark_task_completed_from_car(db, car_id=cars[0].id, task_id=old_task_id)
    assert cars[0].current_task_id == next_cycle["assigned_task_ids"][0]


@pytest.mark.asyncio
async def test_unacknowledged_dispatch_is_released_and_can_be_reassigned(db_session, monkeypatch):
    db = db_session
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, _ = _create_express_and_appointment(db, recipient=customer, customer=customer)

    async def connected(car_id):
        return object()

    async def send(car_id, payload):
        return True

    monkeypatch.setattr("app.services.dispatch_service.get_car_control_connection", connected)
    monkeypatch.setattr("app.services.dispatch_service.send_car_control_message", send)
    service = DispatchService()
    await service.dispatch_pending(db)
    task = db.get(Task, express.task_id)
    command = db.query(DispatchCommand).filter(DispatchCommand.task_id == task.id).one()
    first_command_id = command.command_id
    command.created_at = datetime.utcnow() - timedelta(seconds=21)
    db.commit()

    await service.process_dispatch_commands(db)
    assert command.status == "failed"
    assert task.car_id is None
    assert car.current_task_id is None

    await service.dispatch_pending(db)
    assert task.car_id == car.id
    assert command.status == "pending"
    assert command.command_id != first_command_id


def test_dispatch_ack_is_idempotent_and_rejects_wrong_command(db_session):
    db = db_session
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)
    task = Task(status=TaskStatus.pending, car_id=car.id, user_id=customer.id,
                target_address=appointment.pickup_address, geocoding_status=GeocodingStatus.pending)
    db.add(task)
    db.flush()
    express.task_id = task.id
    car.current_task_id = task.id
    command = DispatchCommand(car_id=car.id, task_id=task.id, status="pending")
    db.add(command)
    db.commit()

    service = DispatchService()
    service.mark_task_accepted_from_car(
        db, car_id=car.id, task_id=task.id, command_id=command.command_id
    )
    acknowledged_at = command.acknowledged_at
    service.mark_task_accepted_from_car(
        db, car_id=car.id, task_id=task.id, command_id=command.command_id
    )
    assert command.acknowledged_at == acknowledged_at
    with pytest.raises(ServiceError) as exc:
        service.mark_task_accepted_from_car(
            db, car_id=car.id, task_id=task.id, command_id="wrong-command"
        )
    assert exc.value.status_code == 409


def test_running_task_uses_disconnect_grace_and_recovers(db_session):
    db = db_session
    customer = _create_recipient_user(db)
    car = _create_car(db)
    express, appointment = _create_express_and_appointment(db, recipient=customer, customer=customer)
    task = Task(status=TaskStatus.running, car_id=car.id, user_id=customer.id,
                target_address=appointment.pickup_address, geocoding_status=GeocodingStatus.pending)
    db.add(task)
    db.flush()
    express.task_id = task.id
    express.status = ExpressStatus.delivering
    car.current_task_id = task.id
    car.task_status = CarTaskStatus.delivering
    car.last_seen_at = datetime.now()
    command = DispatchCommand(car_id=car.id, task_id=task.id, status="accepted",
                              acknowledged_at=datetime.now())
    db.add(command)
    db.commit()

    service = DispatchService()
    service.mark_cars_offline(db, [car.id])
    assert command.status == "accepted"
    assert service.reconcile_running_interruptions(db) == 0

    car.last_seen_at = datetime.now() - timedelta(seconds=31)
    db.commit()
    assert service.reconcile_running_interruptions(db) == 1
    assert command.status == "interrupted"

    service.mark_car_connected(db, car.id)
    service.mark_task_accepted_from_car(
        db, car_id=car.id, task_id=task.id, command_id=command.command_id
    )
    assert command.status == "accepted"
    assert command.interrupted_at is None
    assert car.task_status == CarTaskStatus.delivering


@pytest.mark.asyncio
async def test_heartbeat_expires_silent_control_connection(db_session):
    class FakeWebSocket:
        headers = {}

        def __init__(self):
            self.closed_with = None

        async def close(self, code):
            self.closed_with = code

    websocket = FakeWebSocket()
    await car_ws_manager.register_car_control_connection(42, websocket)
    car_ws_manager._last_seen[42] = datetime.now() - timedelta(seconds=16)

    offline = await car_ws_manager.heartbeat_connections(db_session)

    assert offline == [42]
    assert websocket.closed_with == 1011
    assert await car_ws_manager.get_car_control_connection(42) is None


@pytest.mark.asyncio
async def test_manual_dispatch_requires_admin(db_session):
    customer = _create_recipient_user(db_session)
    with pytest.raises(ServiceError) as exc:
        await DispatchService().run_dispatch_cycle(db_session, customer)
    assert exc.value.status_code == 403


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

