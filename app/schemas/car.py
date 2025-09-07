from pydantic import Field, validator
from typing import Optional
from datetime import datetime
import re

from app.schemas.base import BaseSchema
from app.models.enums import CarTaskStatus
from app.schemas.validators import create_validator, validate_numeric_range
from app.core.constants import NUMERIC_RANGES, FIELD_DESCRIPTIONS


class CarBase(BaseSchema):
    """小车基础模型"""
    task_status: CarTaskStatus = Field(default=CarTaskStatus.idle, description=FIELD_DESCRIPTIONS["task_status"])
    current_task_id: Optional[int] = Field(None, description=FIELD_DESCRIPTIONS["current_task_id"])
    current_speed: float = Field(
        default=0.0,
        description=FIELD_DESCRIPTIONS["current_speed"],
        ge=NUMERIC_RANGES["current_speed"]["min"],
        le=NUMERIC_RANGES["current_speed"]["max"]
    )
    current_latitude: Optional[float] = Field(
        None,
        description=FIELD_DESCRIPTIONS["current_latitude"],
        ge=NUMERIC_RANGES["latitude"]["min"],
        le=NUMERIC_RANGES["latitude"]["max"]
    )
    current_longitude: Optional[float] = Field(
        None,
        description=FIELD_DESCRIPTIONS["current_longitude"],
        ge=NUMERIC_RANGES["longitude"]["min"],
        le=NUMERIC_RANGES["longitude"]["max"]
    )
    battery_level: float = Field(
        default=100.0,
        description=FIELD_DESCRIPTIONS["battery_level"],
        ge=NUMERIC_RANGES["battery_level"]["min"],
        le=NUMERIC_RANGES["battery_level"]["max"]
    )
    running_time: int = Field(default=0, ge=0, description=FIELD_DESCRIPTIONS["running_time"])
    is_active: bool = Field(default=True, description=FIELD_DESCRIPTIONS["is_active"])
    
    # 验证速度
    validate_current_speed = create_validator(
        validate_numeric_range,
        min_value=NUMERIC_RANGES["current_speed"]["min"],
        max_value=NUMERIC_RANGES["current_speed"]["max"],
        field_name="速度",
        round_digits=2
    )
    
    # 验证电量
    validate_battery_level = create_validator(
        validate_numeric_range,
        min_value=NUMERIC_RANGES["battery_level"]["min"],
        max_value=NUMERIC_RANGES["battery_level"]["max"],
        field_name="电量百分比",
        round_digits=2
    )
    
    # 验证纬度
    validate_current_latitude = create_validator(
        validate_numeric_range,
        min_value=NUMERIC_RANGES["latitude"]["min"],
        max_value=NUMERIC_RANGES["latitude"]["max"],
        field_name="纬度",
        round_digits=6
    )
    
    # 验证经度
    validate_current_longitude = create_validator(
        validate_numeric_range,
        min_value=NUMERIC_RANGES["longitude"]["min"],
        max_value=NUMERIC_RANGES["longitude"]["max"],
        field_name="经度",
        round_digits=6
    )


class CarCreate(CarBase):
    """创建小车请求模型"""
    car_number: str = Field(..., max_length=50, description="小车编号")
    
    @validator('car_number')
    @classmethod
    def validate_car_number(cls, v: str) -> str:
        """验证小车编号格式"""
        if not v or len(v.strip()) == 0:
            raise ValueError('小车编号不能为空')
        
        # 小车编号格式：CAR-XXXX
        if not re.match(r'^CAR-\d{4}$', v.strip().upper()):
            raise ValueError('小车编号格式不正确，应为CAR-XXXX格式（如CAR-0001）')
            
        return v.strip().upper()


class CarUpdate(BaseSchema):
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


class CarResponse(BaseSchema):
    """小车响应模型"""
    id: int = Field(..., description="小车ID")
    car_number: str = Field(..., description="小车编号")
    task_status: CarTaskStatus = Field(..., description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    current_speed: float = Field(..., description="当前速度(km/h)")
    current_latitude: Optional[float] = Field(None, description="当前纬度")
    current_longitude: Optional[float] = Field(None, description="当前经度")
    battery_level: float = Field(..., description="电量百分比")
    running_time: int = Field(..., description="已运行时间(分钟)")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    current_task_status: Optional[str] = Field(None, description="当前任务状态")
    current_task_express_count: Optional[int] = Field(None, description="当前任务快递数量")
    
    class Config:
        from_attributes = True


class CarStatusUpdate(BaseSchema):
    """小车状态更新模型"""
    task_status: CarTaskStatus = Field(..., description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    
    class Config:
        # 使用示例
        schema_extra = {
            "example": {
                "task_status": "delivering",
                "current_task_id": 123
            }
        }


class CarLocationUpdate(BaseSchema):
    """小车位置更新模型"""
    current_latitude: float = Field(..., ge=-90.0, le=90.0, description="当前纬度")
    current_longitude: float = Field(..., ge=-180.0, le=180.0, description="当前经度")
    current_speed: Optional[float] = Field(None, ge=0.0, le=50.0, description="当前速度(km/h)")
    battery_level: Optional[float] = Field(None, ge=0.0, le=100.0, description="电量百分比")

    @validator('current_latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """验证纬度范围"""
        if v < -90 or v > 90:
            raise ValueError('纬度必须在-90到90之间')
        return round(v, 6)  # 保留6位小数，精度约1米
    
    @validator('current_longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """验证经度范围"""
        if v < -180 or v > 180:
            raise ValueError('经度必须在-180到180之间')
        return round(v, 6)  # 保留6位小数，精度约1米

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
    
    class Config:
        # 使用示例
        schema_extra = {
            "example": {
                "current_latitude": 39.908823,
                "current_longitude": 116.397470,
                "current_speed": 15.5,
                "battery_level": 85.2
            }
        }