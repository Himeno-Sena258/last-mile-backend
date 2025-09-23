from sqlalchemy import Column, String, ForeignKey, Integer, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.enums import ExpressStatus
from app.models.base import BaseModel

class Express(BaseModel):
    __tablename__ = 'express'    

    recipient_name = Column(String(100), nullable=False, comment='收件人姓名')
    recipient_phone = Column(String(20), nullable=False, comment='收件人电话')
    recipient_address = Column(JSON, nullable=False, comment='收件人地址')
    tracking_number = Column(String(100), unique=True, nullable=False, comment='快递单号')
    pickup_code = Column(String(20), nullable=True, comment='取件码')
    recipient_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='收件人用户ID')
    status = Column(Enum(ExpressStatus), default=ExpressStatus.unassigned, comment='快递状态')
    station_name = Column(String(200), nullable=True, comment='所属驿站名称')
    station_address = Column(String(500), nullable=True, comment='驿站地址')
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True, comment='对应配送任务ID')

    task = relationship('Task', back_populates='express_items')
    appointment = relationship('Appointment', back_populates='express', uselist=False)
    route_steps = relationship('RouteStep', back_populates='express')
    recipient_user = relationship('User', back_populates='express_items', foreign_keys=[recipient_user_id])
