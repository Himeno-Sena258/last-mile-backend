from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.enums import AppointmentStatus


class AppointmentBase(BaseModel):
    """预约基础模型"""
    customer_id: int = Field(..., description="客户ID")
    express_tracking_number: str = Field(..., max_length=100, description="快递单号")
    appointment_time: datetime = Field(..., description="预约时间")
    status: AppointmentStatus = Field(default=AppointmentStatus.scheduled, description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")