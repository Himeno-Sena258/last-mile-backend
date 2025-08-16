from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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