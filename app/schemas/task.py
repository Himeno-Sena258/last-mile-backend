from pydantic import Field, validator, BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import re

from app.schemas.base import BaseSchema
from app.models.enums import TaskStatus
from app.schemas.validators import create_validator, validate_future_datetime, validate_pattern
from app.core.constants import TIME_LIMITS, FIELD_DESCRIPTIONS


class TaskBase(BaseSchema):
    """任务基础模型"""
    status: TaskStatus = Field(default=TaskStatus.pending, description=FIELD_DESCRIPTIONS["status"])
    assigned_car_number: Optional[str] = Field(None, description=FIELD_DESCRIPTIONS["assigned_car_number"])
    expected_completion_time: Optional[datetime] = Field(None, description=FIELD_DESCRIPTIONS["expected_completion_time"])
    route_id: Optional[int] = Field(None, description=FIELD_DESCRIPTIONS["route_id"])
    
    # 验证预计完成时间
    validate_expected_completion_time = create_validator(
        validate_future_datetime,
        max_days=TIME_LIMITS["max_future_days"],
        field_name="预计完成时间"
    )
    
    # 验证小车编号
    validate_assigned_car_number = create_validator(
        validate_pattern,
        pattern="car_number",
        field_name="小车编号"
    )


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
        for tracking_number in v:
            if not tracking_number or len(tracking_number.strip()) == 0:
                raise ValueError('快递单号不能为空')
            
            # 快递单号只能包含字母、数字和连字符
            if not re.match(r'^[A-Za-z0-9\-]+$', tracking_number):
                raise ValueError(f'快递单号格式不正确：{tracking_number}')
        
        # 转换为大写并去除空格
        return [tn.strip().upper() for tn in v]


class TaskUpdate(BaseModel):
    """更新任务请求模型"""
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    assigned_car_number: Optional[str] = Field(None, max_length=50, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
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

    @validator('completed_at')
    @classmethod
    def validate_completed_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """验证完成时间"""
        if v is None:
            return v
            
        # 完成时间不能是未来时间
        if v > datetime.now():
            raise ValueError('完成时间不能是未来时间')
            
        return v

    @validator('assigned_car_number')
    @classmethod
    def validate_car_number(cls, v: Optional[str]) -> Optional[str]:
        """验证小车编号格式"""
        if v is None:
            return v
            
        # 小车编号格式：CAR-XXXX
        if not re.match(r'^CAR-\d{4}$', v.strip().upper()):
            raise ValueError('小车编号格式不正确，应为CAR-XXXX格式（如CAR-0001）')
            
        return v.strip().upper()


class TaskExpressInfo(BaseModel):
    """任务中的快递信息"""
    tracking_number: str = Field(..., description="快递单号")
    recipient_name: str = Field(..., description="收件人姓名")
    recipient_phone: str = Field(..., description="收件人电话")
    recipient_address: str = Field(..., description="收件人地址")
    status: TaskStatus = Field(..., description="快递状态")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: int = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    assigned_car_number: Optional[str] = Field(None, description="分配的小车编号")
    expected_completion_time: Optional[datetime] = Field(None, description="任务预计完成时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    route_id: Optional[int] = Field(None, description="路线ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    express_items: List[TaskExpressInfo] = Field(default=[], description="快递列表")
    car_status: Optional[str] = Field(None, description="小车状态")
    car_battery_level: Optional[float] = Field(None, description="小车电量")
    route_name: Optional[str] = Field(None, description="路线名称")
    route_total_distance: Optional[float] = Field(None, description="路线总距离")
    route_estimated_duration: Optional[int] = Field(None, description="路线预计耗时")
    
    class Config:
        from_attributes = True  # Pydantic v2语法，替代orm_mode


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