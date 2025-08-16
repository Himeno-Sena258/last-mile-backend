from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional


class TaskAssign(BaseModel):
    """任务分配模型"""
    assigned_car_number: str = Field(..., max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    
    @validator('assigned_car_number')
    @classmethod
    def validate_car_number(cls, v: str) -> str:
        """验证小车编号格式"""
        if not v or len(v.strip()) == 0:
            raise ValueError('小车编号不能为空')
            
        # 小车编号格式：CAR-XXXX
        import re
        if not re.match(r'^CAR-\d{4}$', v.strip().upper()):
            raise ValueError('小车编号格式不正确，应为CAR-XXXX格式（如CAR-0001）')
            
        return v.strip().upper()
    
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
    
    class Config:
        # 使用示例
        schema_extra = {
            "example": {
                "assigned_car_number": "CAR-0001",
                "expected_completion_time": "2024-01-20T14:30:00"
            }
        }