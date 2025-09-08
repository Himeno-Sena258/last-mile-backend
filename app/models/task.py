from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.enums import TaskStatus
from app.models.base import BaseModel


class Task(BaseModel):
    __tablename__ = 'tasks'

    status = Column(Enum(TaskStatus), default=TaskStatus.pending, comment='任务状态')
    assigned_car_number = Column(String(50), ForeignKey('cars.car_number'), nullable=True, comment='分配的小车编号')

    expected_completion_time = Column(DateTime(timezone=True), nullable=True, comment='任务预计完成时间')
    completed_at = Column(DateTime(timezone=True), nullable=True, comment='任务完成时间')
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=True, comment='路线ID')
    assigned_car = relationship('Car', foreign_keys=[assigned_car_number], back_populates='assigned_tasks')
    route = relationship('Route', back_populates='tasks')
    express_item = relationship('Express', back_populates='task', uselist = False)

