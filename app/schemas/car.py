from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import CarTaskStatus

class CarBase(BaseModel):
    """小车基础schema"""
    task_status: CarTaskStatus = Field(default=CarTaskStatus.idle, description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    current_speed: float = Field(default=0.0, ge=0, description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, ge=-90, le=90, description="当前纬度")
    current_longitude: Optional[float] = Field(None, ge=-180, le=180, description="当前经度")
    battery_level: float = Field(default=100.0, ge=0, le=100, description="电量百分比")
    running_time: int = Field(default=0, ge=0, description="已经运行时间(分钟)")
    is_active: bool = Field(default=True, description="是否激活")

class CarCreate(BaseModel):
    """创建小车schema"""
    task_status: CarTaskStatus = Field(default=CarTaskStatus.idle, description="任务状态")
    current_speed: float = Field(default=0.0, ge=0, description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, ge=-90, le=90, description="当前纬度")
    current_longitude: Optional[float] = Field(None, ge=-180, le=180, description="当前经度")
    battery_level: float = Field(default=100.0, ge=0, le=100, description="电量百分比")
    running_time: int = Field(default=0, ge=0, description="已经运行时间(分钟)")
    is_active: bool = Field(default=True, description="是否激活")

class CarUpdate(BaseModel):
    """更新小车schema"""
    task_status: Optional[CarTaskStatus] = Field(None, description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    current_speed: Optional[float] = Field(None, ge=0, description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, ge=-90, le=90, description="当前纬度")
    current_longitude: Optional[float] = Field(None, ge=-180, le=180, description="当前经度")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="电量百分比")
    running_time: Optional[int] = Field(None, ge=0, description="已经运行时间(分钟)")
    is_active: Optional[bool] = Field(None, description="是否激活")

class CarResponse(CarBase):
    """小车响应schema"""
    id: int = Field(..., description="小车ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class CarLocationUpdate(BaseModel):
    """小车位置更新schema"""
    current_latitude: float = Field(..., ge=-90, le=90, description="当前纬度")
    current_longitude: float = Field(..., ge=-180, le=180, description="当前经度")
    current_speed: Optional[float] = Field(None, ge=0, description="当前速度(km/h)")

class CarStatusUpdate(BaseModel):
    """小车状态更新schema"""
    task_status: CarTaskStatus = Field(..., description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="电量百分比")
    running_time: Optional[int] = Field(None, ge=0, description="已经运行时间(分钟)")