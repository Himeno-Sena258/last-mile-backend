from pydantic import Field, validator, BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.validators import create_validator, validate_string_length, validate_numeric_range
from app.core.constants import MAX_LENGTHS, NUMERIC_RANGES, FIELD_DESCRIPTIONS


class RouteStepBase(BaseModel):
    """路线步骤基础模型"""
    step_order: int = Field(..., ge=1, description="步骤顺序")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="纬度")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="经度")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    description: Optional[str] = Field(None, max_length=200, description="步骤描述")
    estimated_duration: Optional[int] = Field(None, ge=0, le=1440, description="预计停留时间(分钟)")

    @validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """验证纬度"""
        if v < -90 or v > 90:
            raise ValueError('纬度必须在-90到90之间')
        return round(v, 6)  # 保留6位小数，精度约0.1米
    
    @validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """验证经度"""
        if v < -180 or v > 180:
            raise ValueError('经度必须在-180到180之间')
        return round(v, 6)  # 保留6位小数，精度约0.1米

    @validator('step_order')
    @classmethod
    def validate_step_order(cls, v: int) -> int:
        """验证步骤顺序"""
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


class RouteStepCreate(RouteStepBase):
    """路线步骤创建模型"""
    pass


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


class RouteStepResponse(BaseModel):
    """路线步骤响应模型"""
    id: int = Field(..., description="步骤ID")
    route_id: int = Field(..., description="路线ID")
    step_order: int = Field(..., description="步骤顺序")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    address: Optional[str] = Field(None, description="地址")
    description: Optional[str] = Field(None, description="步骤描述")
    estimated_duration: Optional[int] = Field(None, description="预计停留时间(分钟)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    route_name: Optional[str] = Field(None, description="所属路线名称")
    is_start_point: Optional[bool] = Field(None, description="是否为起点")
    is_end_point: Optional[bool] = Field(None, description="是否为终点")
    
    class Config:
        from_attributes = True


class RouteBase(BaseSchema):
    """路线基础模型"""
    name: Optional[str] = Field(
        None,
        description=FIELD_DESCRIPTIONS["name"],
        max_length=MAX_LENGTHS["route_name"]
    )
    description: Optional[str] = Field(
        None,
        description=FIELD_DESCRIPTIONS["description"],
        max_length=MAX_LENGTHS["description"]
    )
    total_distance: Optional[float] = Field(
        None,
        description=FIELD_DESCRIPTIONS["total_distance"],
        ge=NUMERIC_RANGES["total_distance"]["min"],
        le=NUMERIC_RANGES["total_distance"]["max"]
    )
    estimated_duration: Optional[int] = Field(
        None,
        description=FIELD_DESCRIPTIONS["estimated_duration"],
        ge=NUMERIC_RANGES["estimated_duration"]["min"],
        le=NUMERIC_RANGES["estimated_duration"]["max"]
    )
    
    # 验证总距离
    validate_total_distance = create_validator(
        validate_numeric_range,
        min_value=NUMERIC_RANGES["total_distance"]["min"],
        max_value=NUMERIC_RANGES["total_distance"]["max"],
        field_name="总距离",
        round_digits=2
    )
    
    # 验证预计耗时
    validate_estimated_duration = create_validator(
        validate_numeric_range,
        min_value=NUMERIC_RANGES["estimated_duration"]["min"],
        max_value=NUMERIC_RANGES["estimated_duration"]["max"],
        field_name="预计耗时"
    )
    
    # 验证路线名称
    validate_name = create_validator(
        validate_string_length,
        max_length=MAX_LENGTHS["route_name"],
        field_name="路线名称"
    )
    
    # 验证路线描述
    validate_description = create_validator(
        validate_string_length,
        max_length=MAX_LENGTHS["description"],
        field_name="路线描述"
    )


class RouteCreate(RouteBase):
    """路线创建模型"""
    name: str = Field(..., min_length=1, max_length=200, description="路线名称")
    steps: List[RouteStepCreate] = Field(..., min_items=2, description="路线步骤列表")
    
    @validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证路线名称"""
        if not v or len(v.strip()) == 0:
            raise ValueError('路线名称不能为空')
        return v.strip()
    
    @validator('steps')
    @classmethod
    def validate_steps(cls, v: List[RouteStepCreate]) -> List[RouteStepCreate]:
        """验证路线步骤"""
        if not v or len(v) < 2:
            raise ValueError('路线至少需要包含2个步骤(起点和终点)')
        
        # 验证步骤顺序
        step_orders = [step.step_order for step in v]
        if len(set(step_orders)) != len(step_orders):
            raise ValueError('路线步骤顺序不能重复')
        
        # 验证步骤顺序连续性
        sorted_orders = sorted(step_orders)
        if sorted_orders != list(range(1, len(sorted_orders) + 1)):
            raise ValueError('路线步骤顺序必须从1开始连续递增')
        
        return v


class RouteUpdate(BaseModel):
    """路线更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="路线名称")
    description: Optional[str] = Field(None, description="路线描述")
    total_distance: Optional[float] = Field(None, ge=0.0, le=1000.0, description="总距离(km)")
    estimated_duration: Optional[int] = Field(None, ge=0, le=1440, description="预计耗时(分钟)")

    @validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """验证路线名称"""
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError('路线名称不能为空')
            return v.strip()
        return v

    @validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """验证路线描述"""
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
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


class RouteResponse(BaseModel):
    """路线响应模型"""
    id: int = Field(..., description="路线ID")
    name: str = Field(..., description="路线名称")
    description: Optional[str] = Field(None, description="路线描述")
    total_distance: Optional[float] = Field(None, description="总距离(km)")
    estimated_duration: Optional[int] = Field(None, description="预计耗时(分钟)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    steps: Optional[List[RouteStepResponse]] = Field(None, description="路线步骤列表")
    step_count: Optional[int] = Field(None, description="步骤总数")
    active_task_count: Optional[int] = Field(None, description="使用此路线的活跃任务数")
    
    class Config:
        from_attributes = True