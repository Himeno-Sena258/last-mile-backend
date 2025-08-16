from pydantic import Field, validator
from typing import List
from .route_base import RouteBase
from .route_step_create import RouteStepCreate


class RouteCreate(RouteBase):
    """路线创建模型"""
    name: str = Field(..., min_length=1, max_length=200, description="路线名称")
    steps: List[RouteStepCreate] = Field(..., min_items=2, description="路线步骤列表")
    
    @validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证路线名称"""
        if not v or len(v.strip()) == 0:
            raise ValueError('路线名称不能为空')
        return v.strip()
    
    @validator('steps')
    @classmethod
    def validate_steps(cls, v: List[RouteStepCreate]) -> List[RouteStepCreate]:
        """验证路线步骤"""
        if not v or len(v) < 2:
            raise ValueError('路线至少需要包含2个步骤(起点和终点)')
        
        # 验证步骤顺序
        step_orders = [step.step_order for step in v]
        if len(set(step_orders)) != len(step_orders):
            raise ValueError('路线步骤顺序不能重复')
        
        # 验证步骤顺序连续性
        sorted_orders = sorted(step_orders)
        if sorted_orders != list(range(1, len(sorted_orders) + 1)):
            raise ValueError('路线步骤顺序必须从1开始连续递增')
        
        return v