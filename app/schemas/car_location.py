from datetime import datetime
from typing import Literal, Optional
from pydantic import AwareDatetime, BaseModel, Field


class LocationReport(BaseModel):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    coord_system: Literal["WGS84"] = "WGS84"
    reported_at: AwareDatetime
    speed: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)


class TaskLocationResponse(BaseModel):
    task_id: int
    car_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coord_system: Literal["WGS84"] = "WGS84"
    reported_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    is_stale: bool = True
    state: Literal["unassigned", "waiting", "live", "stale", "inactive"]
