from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import AppointmentStatus, ExpressStatus, UserRole
from app.models.express import Express
from app.models.user import User
from app.models.user_address import Address
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.appointment_service import AppointmentService


def _create_customer(db: Session, username: str = "customer1") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hash",
        name="Customer",
        phone="13800000000",
        address=None,
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
