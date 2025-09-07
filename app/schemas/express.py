from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from app.schemas.base import BaseSchema
from app.models.enums import ExpressStatus
from app.schemas.validators import create_validator, validate_non_empty_string, validate_pattern
from app.core.constants import MAX_LENGTHS, FIELD_DESCRIPTIONS
import re


class ExpressBase(BaseSchema):
    """快递基础模型"""
    tracking_number: str = Field(
        description=FIELD_DESCRIPTIONS["tracking_number"],
        max_length=MAX_LENGTHS["tracking_number"]
    )
    recipient_name: str = Field(
        description=FIELD_DESCRIPTIONS["recipient_name"],
        max_length=MAX_LENGTHS["name"]
    )
    recipient_phone: str = Field(
        description=FIELD_DESCRIPTIONS["recipient_phone"],
        max_length=MAX_LENGTHS["phone"]
    )
    recipient_address: str = Field(
        description=FIELD_DESCRIPTIONS["recipient_address"],
        max_length=MAX_LENGTHS["address"]
    )
    recipient_user_id: Optional[int] = Field(None, description=FIELD_DESCRIPTIONS["recipient_user_id"])
    status: ExpressStatus = Field(default=ExpressStatus.unassigned, description=FIELD_DESCRIPTIONS["status"])
    station_name: Optional[str] = Field(
        None,
        description=FIELD_DESCRIPTIONS["station_name"],
        max_length=MAX_LENGTHS["station_name"]
    )
    station_address: Optional[str] = Field(
        None,
        description=FIELD_DESCRIPTIONS["station_address"],
        max_length=MAX_LENGTHS["station_address"]
    )
    
    # 验证快递单号
    validate_tracking_number = create_validator(
        validate_pattern,
        pattern="tracking_number",
        field_name="快递单号"
    )
    
    # 验证收件人姓名
    validate_recipient_name = create_validator(
        validate_non_empty_string,
        field_name="收件人姓名"
    )
    
    # 验证收件人电话
    validate_recipient_phone = create_validator(
        validate_pattern,
        pattern="phone",
        field_name="收件人电话"
    )
    
    # 验证收件人地址
    validate_recipient_address = create_validator(
        validate_non_empty_string,
        field_name="收件人地址"
    )


class ExpressCreate(ExpressBase):
    """创建快递请求模型"""
    pass  # 继承所有基础验证规则


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

    @field_validator('recipient_phone')
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

    @field_validator('recipient_name')
    @classmethod
    def validate_recipient_name(cls, v: Optional[str]) -> Optional[str]:
        """验证收件人姓名"""
        if v is None:
            return v
        if not v or len(v.strip()) == 0:
            raise ValueError('收件人姓名不能为空')
        return v.strip()

    @field_validator('recipient_address')
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
    
    model_config = {"from_attributes": True}  # Pydantic v2语法，替代orm_mode


class ExpressStationInput(BaseModel):
    """驿站批量录入快递模型"""
    station_name: str = Field(..., max_length=200, description="驿站名称")
    station_address: str = Field(..., max_length=500, description="驿站地址")
    express_list: List[ExpressCreate] = Field(..., min_items=1, max_items=100, description="快递列表")
    
    @field_validator('station_name')
    @classmethod
    def validate_station_name(cls, v: str) -> str:
        """验证驿站名称"""
        if not v or len(v.strip()) == 0:
            raise ValueError('驿站名称不能为空')
        return v.strip()
    
    @field_validator('station_address')
    @classmethod
    def validate_station_address(cls, v: str) -> str:
        """验证驿站地址"""
        if not v or len(v.strip()) == 0:
            raise ValueError('驿站地址不能为空')
        if len(v.strip()) < 10:
            raise ValueError('驿站地址过于简短，请提供详细地址')
        return v.strip()
    
    @field_validator('express_list')
    @classmethod
    def validate_express_list(cls, v: List[ExpressCreate]) -> List[ExpressCreate]:
        """验证快递列表，确保单号不重复"""
        tracking_numbers = [express.tracking_number for express in v]
        if len(tracking_numbers) != len(set(tracking_numbers)):
            raise ValueError('快递单号不能重复')
        return v


class ExpressStatusUpdate(BaseModel):
    """快递状态更新模型"""
    status: ExpressStatus = Field(..., description="快递状态")