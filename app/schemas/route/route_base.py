from pydantic import BaseModel, Field, validator
from typing import Optional


class RouteBase(BaseModel):
    """路线基础模型"""
    name: Optional[str] = Field(None, max_length=200, description="路线名称")
    description: Optional[str] = Field(None, description="路线描述")
    total_distance: Optional[float] = Field(None, ge=0.0, le=1000.0, description="总距离(km)")
    estimated_duration: Optional[int] = Field(None, ge=0, le=1440, description="预计耗时(分钟)")
    
    @validator('total_distance')
    @classmethod
    def validate_total_distance(cls, v: Optional[float]) -> Optional[float]:
        """验证总距离"""
        if v is None:
            return v
        if v < 0:
            raise ValueError('总距离不能为负数')
        if v > 1000:  # 假设最大距离1000km
            raise ValueError('总距离超出最大限制')
        return round(v, 2)
    
    @validator('estimated_duration')
    @classmethod
    def validate_estimated_duration(cls, v: Optional[int]) -> Optional[int]:
        """验证预计耗时"""
        if v is None:
            return v
        if v < 0:
            raise ValueError('预计耗时不能为负数')
        if v > 1440:  # 最大24小时
            raise ValueError('预计耗时不能超过24小时')
        return v
    
    @validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """验证路线名称"""
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
    @validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """验证路线描述"""
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None