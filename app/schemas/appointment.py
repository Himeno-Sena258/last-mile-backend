from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import AppointmentStatus

class AppointmentBase(BaseModel):
    """预约基础schema"""
    customer_id: int = Field(..., description="客户ID")
    express_tracking_number: str = Field(..., max_length=100, description="对应快递单号")
    appointment_time: datetime = Field(..., description="预约时间")
    status: AppointmentStatus = Field(default=AppointmentStatus.scheduled, description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")

class AppointmentCreate(BaseModel):
    """创建预约schema"""
    customer_id: int = Field(..., description="客户ID")
    express_tracking_number: str = Field(..., max_length=100, description="对应快递单号")
    appointment_time: datetime = Field(..., description="预约时间")
    status: AppointmentStatus = Field(default=AppointmentStatus.scheduled, description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")

class AppointmentUpdate(BaseModel):
    """更新预约schema"""
    appointment_time: Optional[datetime] = Field(None, description="预约时间")
    status: Optional[AppointmentStatus] = Field(None, description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")

class AppointmentResponse(AppointmentBase):
    """预约响应schema"""
    id: int = Field(..., description="预约ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class AppointmentStatusUpdate(BaseModel):
    """预约状态更新schema"""
    status: AppointmentStatus = Field(..., description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")

class AppointmentReschedule(BaseModel):
    """预约重新安排schema"""
    appointment_time: datetime = Field(..., description="新的预约时间")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")