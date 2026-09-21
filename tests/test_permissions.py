from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from app.api import router, car_routes
from app.core import security
from app.core.permissions import Permission, has_permission
from app.db.database import get_db
from app.models.car import Car
from app.models.enums import UserRole, ExpressStatus, TaskStatus
from app.models.express import Express
from app.models.task import Task
from app.models.user import User
from app.models.user_address import Address, UserAddress
from app.schemas.address import AddressCreate, AddressUpdate
from app.schemas.appointment import AppointmentCreate
from app.schemas.express import ExpressCreate
from app.schemas.task import TaskCreate
from app.schemas.user import UserCreate, UserUpdate
from app.services.address_service import AddressService
from app.services.appointment_service import AppointmentService
from app.services.express_service import ExpressService
from app.services.task_service import TaskService
from app.services.errors import ServiceError
from app.models.announcement import Announcement
from app.services.announcement_service import AnnouncementService


@pytest.fixture
def users(db_session):
    users = []
    for name, role in [("admin", UserRole.admin), ("alice", UserRole.customer), ("bob", UserRole.customer), ("other", UserRole.others)]:
        user = User(username=name, email=f"{name}@test.com", name=name, phone="123", hashed_password="hash", role=role, is_active=True)
        db_session.add(user)
        users.append(user)
    db_session.commit()
    return users


def test_default_deny_and_inactive_admin(users):
    admin, alice, bob, other = users
    assert has_permission(admin, Permission.DISPATCH)
    assert not has_permission(alice, Permission.DISPATCH)
    assert not has_permission(other, Permission.TASK)
    admin.is_active = False
    assert not has_permission(admin, Permission.DISPATCH)


def test_users_can_clear_email_without_empty_string_uniqueness_conflicts(db_session, users):
    from app.services.user_service import UserService
    admin, alice, bob, other = users
    service = UserService()
    service.update_current_user(db_session, alice, UserUpdate(email=""))
    service.update_current_user(db_session, bob, UserUpdate(email=""))
    assert alice.email is None and bob.email is None


def test_public_announcements_exclude_disabled_items(db_session):
    draft = Announcement(title="Hidden", content="Draft", date="2026-09-18", is_active=False)
    db_session.add(draft)
    db_session.commit()
    service = AnnouncementService()
    assert service.list_announcements(db_session) == []
    with pytest.raises(ServiceError) as exc:
        service.get_announcement(db_session, draft.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_outgoing_device_command_rechecks_credentials(db_session, monkeypatch):
    from app.services import car_ws_manager as manager
    car = Car(car_number="OUTGOING", is_active=True)
    db_session.add(car)
    db_session.commit()
    monkeypatch.setenv(f"CAR_CONTROL_TOKEN_{car.id}", "valid")
    monkeypatch.setattr(manager, "SessionLocal", lambda: type(db_session)(bind=db_session.get_bind()))
    class Socket:
        headers = {"authorization": "Bearer valid"}
        sent = []
        closed = False
        async def send_json(self, payload):
            self.sent.append(payload)
        async def close(self, code):
            self.closed = True
    socket = Socket()
    await manager.register_car_control_connection(car.id, socket)
    try:
        assert await manager.send_car_control_message(car.id, {"type": "test"})
        monkeypatch.setenv(f"CAR_CONTROL_TOKEN_{car.id}", "rotated")
        assert not await manager.send_car_control_message(car.id, {"type": "test"})
        assert len(socket.sent) == 1
        assert socket.closed
    finally:
        await manager.unregister_car_control_connection(car.id, socket)


@pytest.mark.parametrize("values", [{"role": "admin"}, {"is_active": False}])
def test_registration_cannot_set_privileges(values):
    with pytest.raises(ValidationError):
        UserCreate(username="user", name="User", phone="123", password="password", **values)


@pytest.mark.parametrize("values", [{"role": "admin"}, {"is_active": True}, {"username": "admin"}])
def test_profile_rejects_privileged_fields(values):
    with pytest.raises(ValidationError):
        UserUpdate(**values)


def test_task_queries_are_scoped_and_customers_cannot_write(db_session, users):
    admin, alice, bob, other = users
    own = Task(user_id=alice.id, target_address="A", status=TaskStatus.pending)
    foreign = Task(user_id=bob.id, target_address="B", status=TaskStatus.pending)
    db_session.add_all([own, foreign])
    db_session.commit()
    service = TaskService()
    assert [t.id for t in service.list_tasks(db_session, alice)] == [own.id]
    assert len(service.list_tasks(db_session, admin)) == 2
    for caller, task_id in [(alice, foreign.id), (other, own.id)]:
        with pytest.raises(ServiceError) as exc:
            service.get_task(db_session, caller, task_id)
        assert exc.value.status_code == 403
    with pytest.raises(ServiceError):
        service.create_task(db_session, alice, TaskCreate(target_address="A"))


def test_address_ownership_and_shared_mutation(db_session, users):
    admin, alice, bob, other = users
    service = AddressService()
    own = service.create_address(db_session, alice, AddressCreate(address_text="A"))
    foreign = service.create_address(db_session, bob, AddressCreate(address_text="B"))
    legacy = Address(address_text="Unowned")
    db_session.add(legacy)
    db_session.commit()
    assert [a.id for a in service.list_addresses(db_session, alice)] == [own.id]
    assert len(service.list_addresses(db_session, admin)) == 3
    with pytest.raises(ServiceError):
        service.get_address(db_session, alice, foreign.id)
    with pytest.raises(ServiceError):
        service.update_address(db_session, alice, foreign.id, AddressUpdate(address_text="Hijacked"))
    service.update_address(db_session, alice, own.id, AddressUpdate(address_text="Updated"))
    db_session.add(UserAddress(user_id=bob.id, address_id=own.id))
    db_session.commit()
    with pytest.raises(ServiceError):
        service.update_address(db_session, alice, own.id, AddressUpdate(address_text="Shared"))


def test_customer_cannot_inject_delivery_state(db_session, users):
    admin, alice, bob, other = users
    payload = ExpressCreate(recipient_name="Alice", recipient_phone="123", recipient_address="A",
        recipient_user_id=alice.id, tracking_number="TRACK", task_id=123)
    with pytest.raises(ServiceError):
        ExpressService().create_express(db_session, alice, payload)
    payload.task_id = None
    express = ExpressService().create_express(db_session, alice, payload)
    assert [e.id for e in ExpressService().list_express(db_session, alice)] == [express.id]
    assert ExpressService().list_express(db_session, bob) == []
    with pytest.raises(ServiceError):
        AppointmentService().create_appointment(db_session, alice, AppointmentCreate(
            customer_id=alice.id, express_tracking_number="TRACK", pickup_address="A",
            appointment_time=datetime.now(), status="delivered"))


def test_http_token_uses_current_role_and_rejects_inactive_accounts(db_session, users, monkeypatch):
    admin, alice, bob, other = users
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session
    headers = {"Authorization": f"Bearer {security.create_access_token({'sub': admin.username})}"}
    monkeypatch.setattr("app.services.user_service.get_password_hash", lambda _: "hash")
    with TestClient(app) as client:
        assert client.get('/api/users', headers=headers).status_code == 200
        assert client.put('/api/users/me', headers=headers, json={"role": "admin"}).status_code == 422
        assert client.put('/api/users/me', headers=headers, json={"name": "Updated"}).status_code == 200
        assert admin.role == UserRole.admin
        assert client.post('/api/users/register', json={"username": "new", "name": "New", "phone": "123", "password": "password", "role": "admin"}).status_code == 422
        response = client.post('/api/users/register', json={"username": "new", "name": "New", "phone": "123", "password": "password"})
        assert response.status_code == 201
        assert response.json()["role"] == "customer"
        admin.role = UserRole.customer
        db_session.commit()
        assert client.get('/api/users', headers=headers).status_code == 403
        admin.is_active = False
        db_session.commit()
        assert client.get('/api/users/me', headers=headers).status_code == 401
        assert client.post('/api/regeo', json={"latitude": 30, "longitude": 104}).status_code == 401


@pytest.mark.parametrize("channel", ["video", "control"])
def test_device_channels_authenticate_and_recheck_revocation(db_session, monkeypatch, channel):
    car = Car(car_number="SECURE", is_active=True)
    db_session.add(car)
    db_session.commit()
    monkeypatch.setenv(f"CAR_CONTROL_TOKEN_{car.id}", "device-token")
    monkeypatch.setattr(car_routes, "SessionLocal", lambda: type(db_session)(bind=db_session.get_bind()))
    app = FastAPI()
    app.include_router(car_routes.router)
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/cars/{car.id}/{channel}"):
                pass
        with client.websocket_connect(f"/ws/cars/{car.id}/{channel}", headers={"Authorization": "Bearer device-token"}) as ws:
            if channel == "control":
                ws.receive_json()
            ws.send_text("ping")
            assert ws.receive_text() == "pong"
            car.is_active = False
            db_session.commit()
            ws.send_text("ping")
            with pytest.raises(WebSocketDisconnect):
                ws.receive_text()
