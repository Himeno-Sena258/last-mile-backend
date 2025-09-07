from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Route(BaseModel):
    __tablename__ = 'routes'

    name = Column(String(200), nullable=True, comment='路线名称')
    description = Column(Text, nullable=True, comment='路线描述')
    total_distance = Column(Float, nullable=True, comment='总距离(km)')
    estimated_duration = Column(Integer, nullable=True, comment='预计耗时(分钟)')
    tasks = relationship('Task', back_populates='route')
    route_steps = relationship('RouteStep', back_populates='route', order_by='RouteStep.step_order')

class RouteStep(BaseModel):
    __tablename__ = 'route_steps'

    route_id = Column(Integer, ForeignKey('routes.id'), primary_key=True, comment='路线ID')
    step_order = Column(Integer, primary_key=True, comment='步骤顺序')
    pickup_latitude = Column(Float, nullable=True, comment='预约取件位置纬度')
    pickup_longitude = Column(Float, nullable=True, comment='预约取件位置经度')
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=True, comment='预约信息ID')
    express_tracking_number = Column(String(100), ForeignKey('express.tracking_number'), nullable=True, comment='对应快递单号')
    location_description = Column(String(500), nullable=True, comment='位置描述（如街道号等）')
    estimated_arrival_time = Column(DateTime(timezone=True), nullable=True, comment='预计到达时间')
    route = relationship('Route', back_populates='route_steps')
    appointment = relationship('Appointment', back_populates='route_steps')
    express = relationship('Express', back_populates='route_steps')