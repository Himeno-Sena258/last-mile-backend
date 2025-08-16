from pydantic import BaseModel, Field, validator
from typing import Optional
from app.models.enums import ExpressStatus
import re


class ExpressUpdate(BaseModel):
    """更新快递请求模型"""
    recipient_name: Optional[str] = Field(None, max_length=100, description="收件人姓名")
    recipient_phone: Optional[str] = Field(None, max_length=20, description="收件人电话")
    recipient_address: Optional[str] = Field(None, max_length=500, description="收件人地址")
    recipient_user_id: Optional[int] = Field(None, description="收件人用户ID")
    status: Optional[ExpressStatus] = Field(None, description="快递状态")
    station_name: Optional[str] = Field(None, max_length=200, description="所属驿站名称")
    station_address: Optional[str] = Field(None, max_length=500, description="驿站地址")
    task_id: Optional[int] = Field(None, description="对应配送任务ID")
    
    @validator('recipient_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证手机号格式"""
        if v is None:
            return v
        # 简单的手机号验证，支持国内手机号
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, v):
            raise ValueError('手机号格式不正确')
        return v
    
    @validator('recipient_name')
    @classmethod
    def validate_recipient_name(cls, v: Optional[str]) -> Optional[str]:
        """验证收件人姓名"""
        if v is None:
            return v
        if not v or len(v.strip()) == 0:
            raise ValueError('收件人姓名不能为空')
        return v.strip()
    
    @validator('recipient_address')
    @classmethod
    def validate_recipient_address(cls, v: Optional[str]) -> Optional[str]:
        """验证收件人地址"""
        if v is None:
            return v
        if not v or len(v.strip()) == 0:
            raise ValueError('收件人地址不能为空')
        if len(v.strip()) < 10:
            raise ValueError('收件人地址过于简短，请提供详细地址')
        return v.strip()