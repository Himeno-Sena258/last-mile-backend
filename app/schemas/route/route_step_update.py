from pydantic import BaseModel, Field, validator
from typing import Optional


class RouteStepUpdate(BaseModel):
    """路线步骤更新模型"""
    step_order: Optional[int] = Field(None, ge=1, description="步骤顺序")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="经度")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    description: Optional[str] = Field(None, max_length=200, description="步骤描述")
    estimated_duration: Optional[int] = Field(None, ge=0, le=1440, description="预计停留时间(分钟)")
    
    @validator('latitude')
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        """验证纬度"""
        if v is None:
            return v
        if v < -90 or v > 90:
            raise ValueError('纬度必须在-90到90之间')
        return round(v, 6)  # 保留6位小数，精度约0.1米
    
    @validator('longitude')
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        """验证经度"""
        if v is None:
            return v
        if v < -180 or v > 180:
            raise ValueError('经度必须在-180到180之间')
        return round(v, 6)  # 保留6位小数，精度约0.1米
    
    @validator('step_order')
    @classmethod
    def validate_step_order(cls, v: Optional[int]) -> Optional[int]:
        """验证步骤顺序"""
        if v is None:
            return v
        if v < 1:
            raise ValueError('步骤顺序必须从1开始')
        return v
    
    @validator('address')
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        """验证地址"""
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
    @validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """验证步骤描述"""
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
    @validator('estimated_duration')
    @classmethod
    def validate_estimated_duration(cls, v: Optional[int]) -> Optional[int]:
        """验证预计停留时间"""
        if v is None:
            return v
        if v < 0:
            raise ValueError('预计停留时间不能为负数')
        if v > 1440:  # 最大24小时
            raise ValueError('预计停留时间不能超过24小时')
        return v