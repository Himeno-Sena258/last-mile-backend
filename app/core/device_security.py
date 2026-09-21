import os
import secrets
from app.models.car import Car
from app.services.errors import ServiceError


def require_device(db, car_id: int, authorization: str) -> Car:
    expected = os.getenv(f"CAR_CONTROL_TOKEN_{car_id}")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not expected or not secrets.compare_digest(token.encode(), expected.encode()):
        raise ServiceError(status_code=401, detail="无效的设备凭据")
    car = db.get(Car, car_id)
    if not car or not car.is_active:
        raise ServiceError(status_code=403, detail="设备不存在或未启用")
    return car
