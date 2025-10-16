from sqlalchemy import Column, Integer, ForeignKey, Text, Numeric, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserAddress(BaseModel):
    """用户地址模型：存储地址字符串与坐标，一个用户可有多个地址"""
    __tablename__ = 'user_addresses'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    address_text = Column(Text, nullable=False, comment='地址字符串')
    latitude = Column(Numeric(9, 6), nullable=True, comment='纬度')
    longitude = Column(Numeric(9, 6), nullable=True, comment='经度')
    coord_system = Column(String(10), nullable=False, default='WGS84', comment='坐标系统')

    user = relationship('User', back_populates='addresses')