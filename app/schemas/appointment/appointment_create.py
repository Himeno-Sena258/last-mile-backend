from pydantic import Field, validator
from datetime import datetime, timedelta
from typing import Optional
from .appointment_base import AppointmentBase


class AppointmentCreate(AppointmentBase):
    """创建预约请求模型"""
    
    @validator('appointment_time')
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
    
    @validator('notes')
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """验证备注内容"""
        if v and len(v.strip()) == 0:
            return None
        return v