from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Station(BaseModel):
    """驿站实体：规范化存储驿站信息并与地址关联"""
    __tablename__ = 'stations'

    name = Column(String(200), nullable=False, comment='驿站名称')
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=True, comment='驿站地址ID')

    # 关系
    address = relationship('Address')
    express_items = relationship('Express', back_populates='station')

