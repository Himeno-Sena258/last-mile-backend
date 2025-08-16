from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.enums import ExpressStatus


class ExpressResponse(BaseModel):
    """快递响应模型"""
    id: int = Field(..., description="快递ID")
    tracking_number: str = Field(..., description="快递单号")
    recipient_name: str = Field(..., description="收件人姓名")
    recipient_phone: str = Field(..., description="收件人电话")
    recipient_address: str = Field(..., description="收件人地址")
    recipient_user_id: Optional[int] = Field(None, description="收件人用户ID")
    status: ExpressStatus = Field(..., description="快递状态")
    station_name: Optional[str] = Field(None, description="所属驿站名称")
    station_address: Optional[str] = Field(None, description="驿站地址")
    task_id: Optional[int] = Field(None, description="对应配送任务ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    recipient_username: Optional[str] = Field(None, description="收件人用户名")
    task_status: Optional[str] = Field(None, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, description="分配的小车编号")
    
    class Config:
        from_attributes = True  # Pydantic v2语法，替代orm_mode