from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import TaskStatus, GeocodingStatus
from .geocoding import CoordSystem

class TaskBase(BaseModel):
    """任务基础schema"""
    status: TaskStatus = Field(default=TaskStatus.pending, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")
    target_address: str = Field(..., description="目标地址字符串")
    target_latitude: Optional[float] = Field(None, ge=-90, le=90, description="目标地址纬度")
    target_longitude: Optional[float] = Field(None, ge=-180, le=180, description="目标地址经度")
    coord_system: CoordSystem = Field(default=CoordSystem.WGS84, description="坐标系统")
    geocoder_place_id: Optional[str] = Field(None, max_length=64, description="地理编码的place_id")
    geocoder_accuracy_m: Optional[int] = Field(None, ge=0, description="地理编码精度（米）")
    geocoding_status: GeocodingStatus = Field(default=GeocodingStatus.pending, description="地理编码状态")
    geocoded_at: Optional[datetime] = Field(None, description="地理编码完成时间")

class TaskCreate(BaseModel):
    """创建任务schema"""
    status: TaskStatus = Field(default=TaskStatus.pending, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")
    target_address: str = Field(..., description="目标地址字符串")
    target_latitude: Optional[float] = Field(None, ge=-90, le=90, description="目标地址纬度")
    target_longitude: Optional[float] = Field(None, ge=-180, le=180, description="目标地址经度")
    coord_system: CoordSystem = Field(default=CoordSystem.WGS84, description="坐标系统")
    geocoder_place_id: Optional[str] = Field(None, max_length=64, description="地理编码的place_id")
    geocoder_accuracy_m: Optional[int] = Field(None, ge=0, description="地理编码精度（米）")
    geocoding_status: GeocodingStatus = Field(default=GeocodingStatus.pending, description="地理编码状态")
    geocoded_at: Optional[datetime] = Field(None, description="地理编码完成时间")

class TaskUpdate(BaseModel):
    """更新任务schema"""
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")
    target_address: Optional[str] = Field(None, description="目标地址字符串")
    target_latitude: Optional[float] = Field(None, ge=-90, le=90, description="目标地址纬度")
    target_longitude: Optional[float] = Field(None, ge=-180, le=180, description="目标地址经度")
    coord_system: Optional[CoordSystem] = Field(None, description="坐标系统")
    geocoder_place_id: Optional[str] = Field(None, max_length=64, description="地理编码的place_id")
    geocoder_accuracy_m: Optional[int] = Field(None, ge=0, description="地理编码精度（米）")
    geocoding_status: Optional[GeocodingStatus] = Field(None, description="地理编码状态")
    geocoded_at: Optional[datetime] = Field(None, description="地理编码完成时间")

class TaskResponse(TaskBase):
    """任务响应schema"""
    id: int = Field(..., description="任务ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class TaskStatusUpdate(BaseModel):
    """任务状态更新schema"""
    status: TaskStatus = Field(..., description="任务状态")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")