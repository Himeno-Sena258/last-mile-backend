from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional
from app.models.enums import TaskStatus


class TaskBase(BaseModel):
    """任务基础模型"""
    status: TaskStatus = Field(default=TaskStatus.pending, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")
    
    @validator('expected_completion_time')
    @classmethod
    def validate_expected_completion_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """验证预计完成时间"""
        if v is None:
            return v
            
        # 预计完成时间不能是过去时间
        if v <= datetime.now():
            raise ValueError('预计完成时间不能是过去时间')
        
        # 预计完成时间不能超过7天
        max_future_time = datetime.now() + timedelta(days=7)
        if v > max_future_time:
            raise ValueError('预计完成时间不能超过7天')
            
        return v
    
    @validator('assigned_car_number')
    @classmethod
    def validate_car_number(cls, v: Optional[str]) -> Optional[str]:
        """验证小车编号格式"""
        if v is None:
            return v
            
        # 小车编号格式：CAR-XXXX
        import re
        if not re.match(r'^CAR-\d{4}$', v.strip().upper()):
            raise ValueError('小车编号格式不正确，应为CAR-XXXX格式（如CAR-0001）')
            
        return v.strip().upper()