from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel
from app.models.enums import CarTaskStatus

class CarTaskAssignment(BaseModel):
    """任务-小车分配关联：记录历史分配信息，符合3NF"""
    __tablename__ = 'car_task_assignments'

    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False, comment='小车ID')
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='任务ID')
    assigned_at = Column(DateTime, default=datetime.now, nullable=False, comment='分配时间')
    unassigned_at = Column(DateTime, nullable=True, comment='取消分配时间')
    status = Column(Enum(CarTaskStatus), default=CarTaskStatus.assigned, nullable=False, comment='分配状态')

    car = relationship('Car')
    task = relationship('Task')

