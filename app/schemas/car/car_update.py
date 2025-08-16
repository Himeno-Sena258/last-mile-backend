from pydantic import BaseModel, Field, validator
from typing import Optional
from app.models.enums import CarTaskStatus


class CarUpdate(BaseModel):
    """更新小车请求模型"""
    task_status: Optional[CarTaskStatus] = Field(None, description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    current_speed: Optional[float] = Field(None, ge=0.0, le=50.0, description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="当前纬度")
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="当前经度")
    battery_level: Optional[float] = Field(None, ge=0.0, le=100.0, description="电量百分比")
    running_time: Optional[int] = Field(None, ge=0, description="已运行时间(分钟)")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('current_speed')
    @classmethod
    def validate_speed(cls, v: Optional[float]) -> Optional[float]:
        """验证速度范围"""
        if v is None:
            return v
        if v < 0:
            raise ValueError('速度不能为负数')
        if v > 50:  # 假设小车最大速度50km/h
            raise ValueError('速度超出最大限制')
        return round(v, 2)
    
    @validator('battery_level')
    @classmethod
    def validate_battery_level(cls, v: Optional[float]) -> Optional[float]:
        """验证电量百分比"""
        if v is None:
            return v
        if v < 0 or v > 100:
            raise ValueError('电量百分比必须在0-100之间')
        return round(v, 2)
    
    @validator('current_latitude')
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        """验证纬度范围"""
        if v is None:
            return v
        if v < -90 or v > 90:
            raise ValueError('纬度必须在-90到90之间')
        return round(v, 6)  # 保留6位小数，精度约1米
    
    @validator('current_longitude')
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        """验证经度范围"""
        if v is None:
            return v
        if v < -180 or v > 180:
            raise ValueError('经度必须在-180到180之间')
        return round(v, 6)  # 保留6位小数，精度约1米