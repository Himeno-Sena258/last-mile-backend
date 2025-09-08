from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class RouteBase(BaseModel):
    """路线基础schema"""
    name: Optional[str] = Field(None, max_length=200, description="路线名称")
    description: Optional[str] = Field(None, description="路线描述")
    total_distance: Optional[float] = Field(None, ge=0, description="总距离(km)")
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计耗时(分钟)")

class RouteCreate(BaseModel):
    """创建路线schema"""
    name: Optional[str] = Field(None, max_length=200, description="路线名称")
    description: Optional[str] = Field(None, description="路线描述")
    total_distance: Optional[float] = Field(None, ge=0, description="总距离(km)")
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计耗时(分钟)")

class RouteUpdate(BaseModel):
    """更新路线schema"""
    name: Optional[str] = Field(None, max_length=200, description="路线名称")
    description: Optional[str] = Field(None, description="路线描述")
    total_distance: Optional[float] = Field(None, ge=0, description="总距离(km)")
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计耗时(分钟)")

class RouteResponse(RouteBase):
    """路线响应schema"""
    id: int = Field(..., description="路线ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class RouteStepBase(BaseModel):
    """路线步骤基础schema"""
    route_id: int = Field(..., description="路线ID")
    step_order: int = Field(..., ge=1, description="步骤顺序")
    pickup_latitude: Optional[float] = Field(None, ge=-90, le=90, description="预约取件位置纬度")
    pickup_longitude: Optional[float] = Field(None, ge=-180, le=180, description="预约取件位置经度")
    appointment_id: Optional[int] = Field(None, description="预约信息ID")
    express_tracking_number: Optional[str] = Field(None, max_length=100, description="对应快递单号")
    location_description: Optional[str] = Field(None, max_length=500, description="位置描述（如街道号等）")
    estimated_arrival_time: Optional[datetime] = Field(None, description="预计到达时间")

class RouteStepCreate(BaseModel):
    """创建路线步骤schema"""
    route_id: int = Field(..., description="路线ID")
    step_order: int = Field(..., ge=1, description="步骤顺序")
    pickup_latitude: Optional[float] = Field(None, ge=-90, le=90, description="预约取件位置纬度")
    pickup_longitude: Optional[float] = Field(None, ge=-180, le=180, description="预约取件位置经度")
    appointment_id: Optional[int] = Field(None, description="预约信息ID")
    express_tracking_number: Optional[str] = Field(None, max_length=100, description="对应快递单号")
    location_description: Optional[str] = Field(None, max_length=500, description="位置描述（如街道号等）")
    estimated_arrival_time: Optional[datetime] = Field(None, description="预计到达时间")

class RouteStepUpdate(BaseModel):
    """更新路线步骤schema"""
    pickup_latitude: Optional[float] = Field(None, ge=-90, le=90, description="预约取件位置纬度")
    pickup_longitude: Optional[float] = Field(None, ge=-180, le=180, description="预约取件位置经度")
    appointment_id: Optional[int] = Field(None, description="预约信息ID")
    express_tracking_number: Optional[str] = Field(None, max_length=100, description="对应快递单号")
    location_description: Optional[str] = Field(None, max_length=500, description="位置描述（如街道号等）")
    estimated_arrival_time: Optional[datetime] = Field(None, description="预计到达时间")

class RouteStepResponse(RouteStepBase):
    """路线步骤响应schema"""
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class RouteWithStepsResponse(RouteResponse):
    """包含步骤的路线响应schema"""
    route_steps: List[RouteStepResponse] = Field(default=[], description="路线步骤列表")