from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import CarTaskStatus

class CarLogBase(BaseModel):
    """小车日志基础schema"""
    car_id: int = Field(..., description="小车ID")
    logged_at: datetime = Field(..., description="记录时间")
    task_status: CarTaskStatus = Field(..., description="任务状态")
    current_speed: float = Field(default=0.0, ge=0, description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, ge=-90, le=90, description="当前纬度")
    current_longitude: Optional[float] = Field(None, ge=-180, le=180, description="当前经度")
    battery_level: float = Field(..., ge=0, le=100, description="电量百分比")
    running_time: int = Field(default=0, ge=0, description="已运行时间(分钟)")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    log_type: Optional[str] = Field(None, max_length=50, description="日志类型（如：状态变更、位置更新、电量警告等）")
    description: Optional[str] = Field(None, description="日志描述")
    extra_data: Optional[str] = Field(None, description="额外数据（JSON格式）")

class CarLogCreate(BaseModel):
    """创建小车日志schema"""
    car_id: int = Field(..., description="小车ID")
    logged_at: datetime = Field(default_factory=datetime.now, description="记录时间")
    task_status: CarTaskStatus = Field(..., description="任务状态")
    current_speed: float = Field(default=0.0, ge=0, description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, ge=-90, le=90, description="当前纬度")
    current_longitude: Optional[float] = Field(None, ge=-180, le=180, description="当前经度")
    battery_level: float = Field(..., ge=0, le=100, description="电量百分比")
    running_time: int = Field(default=0, ge=0, description="已运行时间(分钟)")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    log_type: Optional[str] = Field(None, max_length=50, description="日志类型（如：状态变更、位置更新、电量警告等）")
    description: Optional[str] = Field(None, description="日志描述")
    extra_data: Optional[str] = Field(None, description="额外数据（JSON格式）")

class CarLogResponse(CarLogBase):
    """小车日志响应schema"""
    id: int = Field(..., description="日志ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class CarLogQuery(BaseModel):
    """小车日志查询schema"""
    car_id: Optional[int] = Field(None, description="小车ID")
    task_status: Optional[CarTaskStatus] = Field(None, description="任务状态")
    log_type: Optional[str] = Field(None, max_length=50, description="日志类型")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")

class CarLogSummary(BaseModel):
    """小车日志汇总schema"""
    car_id: int = Field(..., description="小车ID")
    total_logs: int = Field(..., description="总日志数")
    total_running_time: int = Field(..., description="总运行时间(分钟)")
    average_speed: float = Field(..., description="平均速度(km/h)")
    min_battery_level: float = Field(..., description="最低电量百分比")
    max_battery_level: float = Field(..., description="最高电量百分比")
    status_distribution: dict = Field(..., description="状态分布统计")