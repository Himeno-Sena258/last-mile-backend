from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.car import Car
from app.models.car_location import CarLocation
from app.models.dispatch_command import DispatchCommand
from app.models.enums import TaskStatus
from app.schemas.car_location import LocationReport
from app.services.errors import ServiceError
from app.services.task_service import TaskService


class CarLocationService:
    def record(self, db: Session, car_id: int, payload: LocationReport) -> bool:
        car = db.query(Car).filter(Car.id == car_id).with_for_update().first()
        if not car or not car.is_active:
            raise ServiceError(status_code=404, detail="车辆不存在或未启用")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        reported = payload.reported_at.astimezone(timezone.utc).replace(tzinfo=None)
        if reported > now + timedelta(seconds=30):
            raise ServiceError(status_code=422, detail="位置上报时间超出允许范围")
        location = db.get(CarLocation, car_id)
        if location and reported <= location.reported_at:
            db.rollback()
            return False
        if not location:
            location = CarLocation(car_id=car_id)
            db.add(location)
        location.latitude = car.current_latitude = payload.latitude
        location.longitude = car.current_longitude = payload.longitude
        location.reported_at = reported
        location.received_at = now
        if payload.speed is not None:
            car.current_speed = payload.speed
        db.commit()
        return True

    def get_for_task(self, db, current_user, task_id):
        task = TaskService().get_task(db, current_user, task_id)
        car = db.get(Car, task.car_id) if task.car_id else None
        result = {"task_id": task.id, "car_number": car.car_number if car else None,
                  "is_stale": True, "state": "unassigned" if not car else "waiting"}
        if not car:
            return result
        # Never expose the vehicle's later journeys through an old task.
        if task.status != TaskStatus.running or car.current_task_id != task.id:
            result["state"] = "inactive"
            return result
        command = db.query(DispatchCommand).filter(DispatchCommand.task_id == task.id).first()
        if command and command.status == "interrupted":
            result["state"] = "interrupted"
        location = db.get(CarLocation, car.id)
        if not location:
            return result
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stale = (not car.is_active or
                 now - location.reported_at > timedelta(seconds=15) or
                 now - location.received_at > timedelta(seconds=15))
        location_state = "interrupted" if result["state"] == "interrupted" else ("stale" if stale else "live")
        result.update(latitude=location.latitude, longitude=location.longitude,
                      reported_at=location.reported_at.replace(tzinfo=timezone.utc),
                      received_at=location.received_at.replace(tzinfo=timezone.utc),
                      is_stale=stale, state=location_state)
        return result
