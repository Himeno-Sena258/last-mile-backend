from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.enums import TaskStatus


class TaskBatchItem(BaseModel):
    """批量创建任务项"""
    express_tracking_numbers: List[str] = Field(..., min_items=1, max_items=50, description="快递单号列表")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    
    @validator('express_tracking_numbers')
    @classmethod
    def validate_express_tracking_numbers(cls, v: List[str]) -> List[str]:
        """验证快递单号列表"""
        if not v:
            raise ValueError('快递单号列表不能为空')
        
        # 检查是否有重复的快递单号
        if len(v) != len(set(v)):
            raise ValueError('快递单号不能重复')
        
        # 验证每个快递单号格式
        import re
        for tracking_number in v:
            if not tracking_number or len(tracking_number.strip()) == 0:
                raise ValueError('快递单号不能为空')
            
            # 快递单号只能包含字母、数字和连字符
            if not re.match(r'^[A-Za-z0-9\-]+$', tracking_number):
                raise ValueError(f'快递单号格式不正确：{tracking_number}')
        
        # 转换为大写并去除空格
        return [tn.strip().upper() for tn in v]
    
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


class TaskBatchCreate(BaseModel):
    """批量创建任务请求模型"""
    tasks: List[TaskBatchItem] = Field(..., min_items=1, max_items=20, description="任务列表")
    
    @validator('tasks')
    @classmethod
    def validate_tasks(cls, v: List[TaskBatchItem]) -> List[TaskBatchItem]:
        """验证任务列表，确保快递单号不重复"""
        all_tracking_numbers = []
        for task in v:
            all_tracking_numbers.extend(task.express_tracking_numbers)
        
        if len(all_tracking_numbers) != len(set(all_tracking_numbers)):
            raise ValueError('批量任务中的快递单号不能重复')
        
        return v