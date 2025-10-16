from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Enum, Text, Numeric, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.enums import TaskStatus, GeocodingStatus
from app.models.base import BaseModel


class Task(BaseModel):
    __tablename__ = 'tasks'

    status = Column(Enum(TaskStatus), default=TaskStatus.pending, comment='任务状态')
    assigned_car_number = Column(String(50), ForeignKey('cars.car_number'), nullable=True, comment='分配的小车编号')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    target_address = Column(Text, nullable=False, comment='目标地址')
    target_latitude = Column(Numeric(9, 6), nullable=True, comment='目标地址纬度')
    target_longitude = Column(Numeric(9, 6), nullable=True, comment='目标地址经度')
    coord_system = Column(String(10), nullable=False, default='WGS84', comment='坐标系统')
    geocoder_place_id = Column(String(64), nullable=True, comment='地理编码的place_id')
    geocoder_accuracy_m = Column(Float, nullable=True, comment='地理编码精度（米）')
    geocoding_status = Column(Enum(GeocodingStatus), default=GeocodingStatus.pending, comment='地理编码状态')
    geocoded_at = Column(DateTime(timezone=True), nullable=True, comment='地理编码完成时间')
    expected_completion_time = Column(DateTime(timezone=True), nullable=True, comment='任务预计完成时间')
    completed_at = Column(DateTime(timezone=True), nullable=True, comment='任务完成时间')
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=True, comment='路线ID')
    assigned_car = relationship('Car', foreign_keys=[assigned_car_number], back_populates='assigned_tasks')
    user = relationship('User', back_populates='tasks')
    route = relationship('Route', back_populates='tasks')
    express_item = relationship('Express', back_populates='task', uselist = False)

