from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional
from app.models.enums import AppointmentStatus


class AppointmentUpdate(BaseModel):
    """更新预约请求模型"""
    appointment_time: Optional[datetime] = Field(None, description="预约时间")
    status: Optional[AppointmentStatus] = Field(None, description="预约状态")
    notes: Optional[str] = Field(None, max_length=500, description="预约备注")
    
    @validator('appointment_time')
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
    
    @validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """验证备注内容"""
        if v and len(v.strip()) == 0:
            return None
        return v