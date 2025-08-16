from pydantic import BaseModel, Field
from typing import Optional
from app.models.enums import CarTaskStatus


class CarStatusUpdate(BaseModel):
    """小车状态更新模型"""
    task_status: CarTaskStatus = Field(..., description="任务状态")
    current_task_id: Optional[int] = Field(None, description="当前任务ID")
    
    class Config:
        # 使用示例
        schema_extra = {
            "example": {
                "task_status": "delivering",
                "current_task_id": 123
            }
        }