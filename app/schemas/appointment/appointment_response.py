from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.enums import AppointmentStatus


class AppointmentResponse(BaseModel):
    """预约响应模型"""
    id: int = Field(..., description="预约ID")
    customer_id: int = Field(..., description="客户ID")
    express_tracking_number: str = Field(..., description="快递单号")
    appointment_time: datetime = Field(..., description="预约时间")
    status: AppointmentStatus = Field(..., description="预约状态")
    notes: Optional[str] = Field(None, description="预约备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    customer_username: Optional[str] = Field(None, description="客户用户名")
    express_recipient_name: Optional[str] = Field(None, description="收件人姓名")
    express_recipient_address: Optional[str] = Field(None, description="收件人地址")
    
    class Config:
        from_attributes = True  # Pydantic v2语法，替代orm_mode