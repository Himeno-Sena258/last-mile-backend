from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.enums import CarTaskStatus


class CarResponse(BaseModel):
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