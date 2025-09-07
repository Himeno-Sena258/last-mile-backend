from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Enum
from sqlalchemy.orm import relationship
from app.models.enums import AppointmentStatus
from app.models.base import BaseModel

class Appointment(BaseModel):
    __tablename__ = 'appointments'

    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='客户ID')
    express_tracking_number = Column(String(100), ForeignKey('express.tracking_number'), nullable=False, comment='对应快递单号')
    appointment_time = Column(DateTime, nullable=False, comment='预约时间')
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled, comment='预约状态')
    notes = Column(String(500), nullable=True, comment='预约备注')

    customer = relationship('User', back_populates='appointments')
    express = relationship('Express', back_populates='appointment')
    route_steps = relationship('RouteStep', back_populates='appointment')