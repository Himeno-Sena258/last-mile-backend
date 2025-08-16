from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.enums import TaskStatus


class TaskExpressInfo(BaseModel):
    """任务中的快递信息"""
    tracking_number: str = Field(..., description="快递单号")
    recipient_name: str = Field(..., description="收件人姓名")
    recipient_phone: str = Field(..., description="收件人电话")
    recipient_address: str = Field(..., description="收件人地址")
    status: str = Field(..., description="快递状态")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: int = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    assigned_car_number: Optional[str] = Field(None, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    express_items: List[TaskExpressInfo] = Field(default=[], description="快递列表")
    car_status: Optional[str] = Field(None, description="小车状态")
    car_battery_level: Optional[float] = Field(None, description="小车电量")
    route_name: Optional[str] = Field(None, description="路线名称")
    route_total_distance: Optional[float] = Field(None, description="路线总距离")
    route_estimated_duration: Optional[int] = Field(None, description="路线预计耗时")
    
    class Config:
        from_attributes = True  # Pydantic v2语法，替代orm_mode