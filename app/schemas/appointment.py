from datetime import datetime, timedelta
from typing import Optional
from pydantic import EmailStr, Field, field_validator, model_validator, computed_field, BaseModel
from app.schemas.base import BaseSchema
from app.models.enums import AppointmentStatus
from app.schemas.validators import create_validator, validate_non_empty_string, validate_string_length, validate_pattern, validate_future_datetime
from app.core.constants import MAX_LENGTHS, MIN_LENGTHS, TIME_LIMITS, FIELD_DESCRIPTIONS


class AppointmentBase(BaseSchema):
    """预约基础模型"""
    customer_id: int = Field(description=FIELD_DESCRIPTIONS["customer_id"])
    express_tracking_number: str = Field(
        description=FIELD_DESCRIPTIONS["express_tracking_number"],
        max_length=MAX_LENGTHS["tracking_number"]
    )
    appointment_time: datetime = Field(description=FIELD_DESCRIPTIONS["appointment_time"])
    status: AppointmentStatus = Field(
        default=AppointmentStatus.scheduled,
        description=FIELD_DESCRIPTIONS["status"]
    )
    notes: Optional[str] = Field(
        None,
        description=FIELD_DESCRIPTIONS["notes"],
        max_length=MAX_LENGTHS["notes"]
    )
    
    # 验证预约时间
    validate_appointment_time = create_validator(
        validate_future_datetime,
        max_days=TIME_LIMITS["max_future_days"],
        field_name="预约时间"
    )
    
    # 验证快递单号
    validate_express_tracking_number = create_validator(
        validate_pattern,
        pattern="tracking_number",
        field_name="快递单号"
    )
    
    # 验证备注
    validate_notes = create_validator(
        validate_string_length,
        max_length=MAX_LENGTHS["notes"],
        field_name="备注"
    )


class AppointmentCreate(AppointmentBase):
    """创建预约请求模型"""
    
    @field_validator('appointment_time')
    @classmethod
    def validate_appointment_time(cls, v: datetime) -> datetime:
        """验证预约时间必须是未来时间"""
        if v <= datetime.now():
            raise ValueError('预约时间必须是未来时间')
        
        # 预约时间不能超过30天
        max_future_time = datetime.now() + timedelta(days=30)
        if v > max_future_time:
            raise ValueError('预约时间不能超过30天')
            
        return v
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """验证备注内容"""
        if v and len(v.strip()) == 0:
            return None
        return v


class AppointmentUpdate(BaseModel):
    """更新预约请求模型"""
    appointment_time: Optional[datetime] = Field(None, description="预约时间")
    status: Optional[AppointmentStatus] = Field(None, description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")
    
    @field_validator('appointment_time')
    @classmethod
    def validate_appointment_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """验证预约时间必须是未来时间"""
        if v is None:
            return v
            
        if v <= datetime.now():
            raise ValueError('预约时间必须是未来时间')
        
        # 预约时间不能超过30天
        max_future_time = datetime.now() + timedelta(days=30)
        if v > max_future_time:
            raise ValueError('预约时间不能超过30天')
            
        return v
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """验证备注内容"""
        if v and len(v.strip()) == 0:
            return None
        return v


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
    
    model_config = {"from_attributes": True}  # Pydantic v2语法，替代orm_mode


class AppointmentStatusUpdate(BaseModel):
    """预约状态更新模型"""
    status: AppointmentStatus = Field(..., description="预约状态")


class AppointmentTimeUpdate(BaseModel):
    """预约时间更新模型"""
    appointment_time: datetime = Field(..., description="预约时间")
    
    @field_validator('appointment_time')
    @classmethod
    def validate_appointment_time(cls, v: datetime) -> datetime:
        """验证预约时间必须是未来时间"""
        if v <= datetime.now():
            raise ValueError('预约时间必须是未来时间')
        
        # 预约时间不能超过30天
        max_future_time = datetime.now() + timedelta(days=30)
        if v > max_future_time:
            raise ValueError('预约时间不能超过30天')
            
        return v