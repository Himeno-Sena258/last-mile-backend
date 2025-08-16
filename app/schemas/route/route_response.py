from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .route_step_response import RouteStepResponse


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