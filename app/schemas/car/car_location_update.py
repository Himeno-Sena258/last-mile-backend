from pydantic import BaseModel, Field, validator
from typing import Optional


class CarLocationUpdate(BaseModel):
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