from pydantic import Field, validator
from typing import List
from .task_base import TaskBase


class TaskCreate(TaskBase):
    """创建任务请求模型"""
    express_tracking_numbers: List[str] = Field(..., min_items=1, max_items=50, description="快递单号列表")
    
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