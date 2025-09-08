from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.enums import ExpressStatus

class ExpressBase(BaseModel):
    """快递基础schema"""
    recipient_name: str = Field(..., max_length=100, description="收件人姓名")
    recipient_phone: str = Field(..., max_length=20, description="收件人电话")
    recipient_address: str = Field(..., max_length=500, description="收件人地址")
    recipient_user_id: int = Field(..., description="收件人用户ID")
    status: ExpressStatus = Field(default=ExpressStatus.unassigned, description="快递状态")
    station_name: Optional[str] = Field(None, max_length=200, description="所属驿站名称")
    station_address: Optional[str] = Field(None, max_length=500, description="驿站地址")
    task_id: Optional[int] = Field(None, description="对应配送任务ID")

class ExpressCreate(BaseModel):
    """创建快递schema"""
    recipient_name: str = Field(..., max_length=100, description="收件人姓名")
    recipient_phone: str = Field(..., max_length=20, description="收件人电话")
    recipient_address: str = Field(..., max_length=500, description="收件人地址")
    recipient_user_id: int = Field(..., description="收件人用户ID")
    status: ExpressStatus = Field(default=ExpressStatus.unassigned, description="快递状态")
    station_name: Optional[str] = Field(None, max_length=200, description="所属驿站名称")
    station_address: Optional[str] = Field(None, max_length=500, description="驿站地址")
    task_id: Optional[int] = Field(None, description="对应配送任务ID")

class ExpressUpdate(BaseModel):
    """更新快递schema"""
    recipient_name: Optional[str] = Field(None, max_length=100, description="收件人姓名")
    recipient_phone: Optional[str] = Field(None, max_length=20, description="收件人电话")
    recipient_address: Optional[str] = Field(None, max_length=500, description="收件人地址")
    status: Optional[ExpressStatus] = Field(None, description="快递状态")
    station_name: Optional[str] = Field(None, max_length=200, description="所属驿站名称")
    station_address: Optional[str] = Field(None, max_length=500, description="驿站地址")
    task_id: Optional[int] = Field(None, description="对应配送任务ID")

class ExpressResponse(ExpressBase):
    """快递响应schema"""
    id: int = Field(..., description="快递ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class ExpressStatusUpdate(BaseModel):
    """快递状态更新schema"""
    status: ExpressStatus = Field(..., description="快递状态")
    station_name: Optional[str] = Field(None, max_length=200, description="所属驿站名称")
    station_address: Optional[str] = Field(None, max_length=500, description="驿站地址")
