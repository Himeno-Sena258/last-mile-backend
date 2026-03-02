from sqlalchemy import Column, String, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from app.models.enums import ExpressStatus
from app.models.base import BaseModel


class Express(BaseModel):
    __tablename__ = 'express'

    recipient_name = Column(String(100), nullable=False, comment='收件人姓名')
    recipient_phone = Column(String(20), nullable=False, comment='收件人电话')
    # 规范化：改为地址主键外键
    recipient_address_id = Column(Integer, ForeignKey('addresses.id'), nullable=True, comment='收件人地址ID')
    tracking_number = Column(String(100), unique=True, nullable=False, comment='快递单号')
    pickup_code = Column(String(20), nullable=True, comment='取件码')
    recipient_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='收件人用户ID')
    status = Column(Enum(ExpressStatus), default=ExpressStatus.unassigned, comment='快递状态')
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True, comment='对应配送任务ID')

    # 与任务的一对一关系：统一 back_populates 名称为 'express'
    task = relationship('Task', back_populates='express')
    appointment = relationship('Appointment', back_populates='express', uselist=False)
    recipient_user = relationship('User', back_populates='express_items', foreign_keys=[recipient_user_id])
    recipient_address = relationship('Address')
