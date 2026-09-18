from __future__ import annotations

from datetime import datetime, timedelta
import pytest

from sqlalchemy.orm import Session

from app.models.enums import AppointmentStatus, ExpressStatus, UserRole
from app.models.express import Express
from app.models.user import User
from app.models.user_address import Address
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.appointment_service import AppointmentService
from app.services.dispatch_service import DispatchService
from app.services.errors import ServiceError
from app.models.task import Task
from app.models.enums import TaskStatus
from app.schemas.appointment import AppointmentReschedule, AppointmentStatusUpdate


def _create_customer(db: Session, username: str = "customer1") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hash",
        name="Customer",
        phone="13800000000",
        role=UserRole.customer,
        is_active=True,
        avatar_url=None,
    )
    db.add(user)
    db.flush()
    return user


def _create_address(db: Session, text: str = "Shenzhen Nanshan") -> Address:
    address = Address(address_text=text, latitude=None, longitude=None, coord_system="WGS84")
    db.add(address)
    db.flush()
    return address


def _create_express_for_user(db: Session, user: User, tracking_number: str = "TRACK-APPT-001") -> Express:
    addr = _create_address(db)
    express = Express(
        recipient_name="Tom",
        recipient_phone="13800000001",
        recipient_address_id=addr.id,
        tracking_number=tracking_number,
        pickup_code=None,
        recipient_user_id=user.id,
        status=ExpressStatus.unassigned,
        task_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(express)
    db.flush()
    return express


def test_create_appointment_persists_pickup_address(db_session: Session):
    db = db_session
    current_user = _create_customer(db)
    express = _create_express_for_user(db, current_user)

    payload = AppointmentCreate(
        customer_id=current_user.id,
        express_tracking_number=express.tracking_number,
        pickup_address="Shenzhen Nanshan Park Road 1",
        appointment_time=datetime.now() + timedelta(hours=2),
        status=AppointmentStatus.scheduled,
        notes="call before arrive",
    )

    service = AppointmentService()
    appointment = service.create_appointment(db=db, current_user=current_user, payload=payload)

    assert appointment.pickup_address == payload.pickup_address
    assert appointment.express_id == express.id


@pytest.mark.asyncio
async def test_pending_task_tracks_reschedule_and_cancellation(db_session):
    db = db_session
    customer = _create_customer(db)
    express = _create_express_for_user(db, customer)
    service = AppointmentService()
    payload = AppointmentCreate(customer_id=customer.id, express_tracking_number=express.tracking_number,
        pickup_address="A", appointment_time=datetime.now())
    appointment = service.create_appointment(db, customer, payload)
    with pytest.raises(ServiceError) as exc:
        service.create_appointment(db, customer, payload)
    assert exc.value.status_code == 409
    db.rollback()
    await DispatchService().dispatch_pending(db)
    task = db.get(Task, express.task_id)
    new_time = datetime.now() + timedelta(hours=1)
    service.reschedule_appointment(db, customer, appointment.id, AppointmentReschedule(appointment_time=new_time))
    assert task.expected_completion_time == new_time
    service.update_appointment(db, customer, appointment.id, AppointmentUpdate(pickup_address="B"))
    assert task.target_address == "B"
    service.update_appointment_status(db, customer, appointment.id, AppointmentStatusUpdate(status=AppointmentStatus.cancelled))
    assert task.status == TaskStatus.cancelled
    assert express.task_id is None
    result = await DispatchService().dispatch_pending(db)
    assert not result["created_task_ids"]


def test_cannot_appoint_another_users_express(db_session):
    db = db_session
    owner = _create_customer(db, "owner")
    other = _create_customer(db, "other")
    express = _create_express_for_user(db, owner)
    with pytest.raises(ServiceError) as exc:
        AppointmentService().create_appointment(db, other, AppointmentCreate(
            customer_id=other.id, express_tracking_number=express.tracking_number,
            pickup_address="A", appointment_time=datetime.now()))
    assert exc.value.status_code == 403


def test_update_appointment_can_change_pickup_address(db_session: Session):
    db = db_session
    current_user = _create_customer(db, username="customer2")
    express = _create_express_for_user(db, current_user, tracking_number="TRACK-APPT-002")

    service = AppointmentService()
    created = service.create_appointment(
        db=db,
        current_user=current_user,
        payload=AppointmentCreate(
            customer_id=current_user.id,
            express_tracking_number=express.tracking_number,
            pickup_address="Old Address",
            appointment_time=datetime.now() + timedelta(hours=1),
            status=AppointmentStatus.scheduled,
            notes=None,
        ),
    )

    updated = service.update_appointment(
        db=db,
        current_user=current_user,
        appointment_id=created.id,
        payload=AppointmentUpdate(pickup_address="New Address"),
    )

    assert updated.pickup_address == "New Address"
