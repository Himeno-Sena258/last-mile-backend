from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Enum
from sqlalchemy.orm import relationship
from app.models.enums import AppointmentStatus
from app.models.base import BaseModel

class Appointment(BaseModel):
    __tablename__ = 'appointments'

    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='客户ID')
    # 改为使用主键外键：express_id
    express_id = Column(Integer, ForeignKey('express.id'), nullable=False, comment='对应快递ID')
    pickup_address = Column(String(255), nullable=False, comment='取件地址')
    appointment_time = Column(DateTime, nullable=False, comment='预约时间')
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled, comment='预约状态')
    notes = Column(String(500), nullable=True, comment='预约备注')
    
    customer = relationship('User', back_populates='appointments')
    express = relationship('Express', back_populates='appointment')

    @property
    def express_tracking_number(self):
        """兼容旧接口字段：返回快递单号。"""
        try:
            return self.express.tracking_number if self.express else ""
        except Exception:
            return ""
