from sqlalchemy import Column, Boolean, Float, ForeignKey, Integer, Enum, String

from sqlalchemy.orm import relationship
from app.models.enums import CarTaskStatus
from app.models.base import BaseModel

class Car(BaseModel):
    __tablename__ = 'cars'

    car_number = Column(String(50), unique=True, nullable=False, comment='小车编号')
    task_status = Column(Enum(CarTaskStatus), default=CarTaskStatus.idle, comment='任务状态')
    current_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True, comment='当前任务ID')
    current_speed = Column(Float, default=0.0, comment='当前速度(km/h)')
    current_latitude = Column(Float, nullable=True, comment='当前纬度')
    current_longitude = Column(Float, nullable=True, comment='当前经度')
    battery_level = Column(Float, default=100.0, comment='电量百分比')
    running_time = Column(Integer, default=0, comment='已经运行时间(分钟)')
    is_active = Column(Boolean, default=True, comment='是否激活')

    current_task = relationship('Task', foreign_keys=[current_task_id])
    assigned_tasks = relationship('Task', foreign_keys='Task.assigned_car_number', back_populates='assigned_car')
    car_logs = relationship('CarLog', back_populates='car')
