from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer, Enum
from sqlalchemy.orm import relationship
from app.models.enums import CarTaskStatus
from datetime import datetime
from app.models.base import BaseModel

class CarLog(BaseModel):
    __tablename__ = 'car_logs'

    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False, comment='小车编号')
    logged_at = Column(DateTime, default = datetime.now, comment='记录时间')
    task_status = Column(Enum(CarTaskStatus), nullable=False, comment='任务状态')
    current_speed = Column(Float, default=0.0, comment='当前速度(km/h)')
    current_latitude = Column(Float, nullable=True, comment='当前纬度')
    current_longitude = Column(Float, nullable=True, comment='当前经度')
    battery_level = Column(Float, nullable=False, comment='电量百分比')
    running_time = Column(Integer, default=0, comment='已运行时间(分钟)')
    current_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True, comment='当前任务ID')
    log_type = Column(String(50), nullable=True, comment='日志类型（如：状态变更、位置更新、电量警告等）')
    description = Column(Text, nullable=True, comment='日志描述')
    extra_data = Column(Text, nullable=True, comment='额外数据（JSON格式）')

    car = relationship('Car', back_populates='car_logs')
    task = relationship('Task', foreign_keys=[current_task_id])