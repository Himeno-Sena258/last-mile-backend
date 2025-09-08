from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import TaskStatus

class TaskBase(BaseModel):
    """任务基础schema"""
    status: TaskStatus = Field(default=TaskStatus.pending, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")

class TaskCreate(BaseModel):
    """创建任务schema"""
    status: TaskStatus = Field(default=TaskStatus.pending, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")

class TaskUpdate(BaseModel):
    """更新任务schema"""
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")

class TaskResponse(TaskBase):
    """任务响应schema"""
    id: int = Field(..., description="任务ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class TaskStatusUpdate(BaseModel):
    """任务状态更新schema"""
    status: TaskStatus = Field(..., description="任务状态")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")