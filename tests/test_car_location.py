from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import car_routes, task_routes
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.car import Car
from app.models.car_location import CarLocation
from app.models.enums import CarTaskStatus, TaskStatus, UserRole
from app.models.task import Task
from app.models.user import User
from app.schemas.car_location import LocationReport
from app.services.car_location_service import CarLocationService
from app.services.errors import ServiceError


@pytest.fixture
def tracking(db_session):
    db = db_session
    owner = User(username="owner", name="Owner", email="owner@test.com", hashed_password="hash", role=UserRole.customer, is_active=True)
    other = User(username="other", name="Other", email="other@test.com", hashed_password="hash", role=UserRole.customer, is_active=True)
    car = Car(car_number="TRACK-CAR", is_active=True, task_status=CarTaskStatus.delivering)
    db.add_all([owner, other, car])
    db.flush()
    task = Task(user_id=owner.id, car_id=car.id, target_address="A", status=TaskStatus.running)
    db.add(task)
    db.flush()
    car.current_task_id = task.id
    db.commit()
    return db, owner, other, car, task


def report(**kwargs):
    return LocationReport(latitude=30.7, longitude=103.9, reported_at=datetime.now(timezone.utc), **kwargs)


def test_location_updates_permissions_and_old_tasks(tracking):
    db, owner, other, car, task = tracking
    service = CarLocationService()
    assert service.get_for_task(db, owner, task.id)["state"] == "waiting"
    assert service.record(db, car.id, report())
    result = service.get_for_task(db, owner, task.id)
    assert result["state"] == "live"
    assert result["latitude"] == car.current_latitude == 30.7
    with pytest.raises(ServiceError) as exc:
        service.get_for_task(db, other, task.id)
    assert exc.value.status_code == 403
    task.status = TaskStatus.completed
    db.commit()
    result = service.get_for_task(db, owner, task.id)
    assert result["state"] == "inactive"
    assert "latitude" not in result


def test_out_of_order_and_stale_reports(tracking):
    db, owner, other, car, task = tracking
    service = CarLocationService()
    payload = report()
    assert service.record(db, car.id, payload)
    assert not service.record(db, car.id, payload)
    older = payload.model_copy(update={"reported_at": payload.reported_at - timedelta(seconds=1), "latitude": 10})
    assert not service.record(db, car.id, older)
    assert car.current_latitude == 30.7
    location = db.get(CarLocation, car.id)
    location.reported_at -= timedelta(seconds=20)
    db.commit()
    assert service.get_for_task(db, owner, task.id)["state"] == "stale"


@pytest.mark.parametrize("values", [{"latitude": 91}, {"longitude": -181}, {"latitude": float("nan")}, {"coord_system": "GCJ-02"}, {"reported_at": datetime.now()}])
def test_invalid_reports(values):
    payload = {"latitude": 30, "longitude": 104, "reported_at": datetime.now(timezone.utc)}
    payload.update(values)
    with pytest.raises(ValidationError):
        LocationReport(**payload)


def test_future_report_rejected(tracking):
    db, owner, other, car, task = tracking
    payload = report().model_copy(update={"reported_at": datetime.now(timezone.utc) + timedelta(minutes=1)})
    with pytest.raises(ServiceError) as exc:
        CarLocationService().record(db, car.id, payload)
    assert exc.value.status_code == 422


def test_websocket_to_task_location_api(tracking, monkeypatch):
    db, owner, other, car, task = tracking
    monkeypatch.setenv(f"CAR_CONTROL_TOKEN_{car.id}", "test-device-token")
    monkeypatch.setattr(car_routes, "SessionLocal", lambda: type(db)(bind=db.get_bind()))
    app = FastAPI()
    app.include_router(car_routes.router)
    app.include_router(task_routes.router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: owner
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/cars/{car.id}/control", headers={"authorization": "Bearer test-device-token"}) as ws:
            assert ws.receive_json()["type"] == "control_placeholder"
            ws.send_json({"type": "location_update", **report().model_dump(mode="json")})
            ack = ws.receive_json()
            assert ack["ok"] and ack["accepted"]
            response = client.get(f"/api/tasks/{task.id}/location")
            assert response.status_code == 200
            assert response.json()["state"] == "live"
            assert response.json()["latitude"] == 30.7
            next_report = report().model_dump(mode="json")
            next_report["latitude"] = 30.71
            ws.send_json({"type": "location_update", **next_report})
            assert ws.receive_json()["accepted"]
            db.expire_all()
            assert client.get(f"/api/tasks/{task.id}/location").json()["latitude"] == 30.71
            ws.send_json({"type": "location_update", "latitude": 999})
            assert not ws.receive_json()["ok"]
        app.dependency_overrides[get_current_user] = lambda: other
        assert client.get(f"/api/tasks/{task.id}/location").status_code == 403
        from starlette.websockets import WebSocketDisconnect
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/cars/{car.id}/control"):
                pass
