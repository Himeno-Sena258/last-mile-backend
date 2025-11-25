from sqlalchemy import Column, Integer, ForeignKey, Text, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Address(BaseModel):
    """地址实体表：存储地址文本与坐标信息，独立于用户"""
    __tablename__ = 'addresses'

    address_text = Column(Text, nullable=False, comment='地址字符串')
    latitude = Column(Numeric(9, 6), nullable=True, comment='纬度')
    longitude = Column(Numeric(9, 6), nullable=True, comment='经度')
    coord_system = Column(String(10), nullable=False, default='WGS84', comment='坐标系统')

    # 多对多：通过关联表连接到用户
    users = relationship('User', secondary='user_addresses', back_populates='addresses')


class UserAddress(BaseModel):
    """用户-地址关联表：连接用户与地址，实现多对多关系"""
    __tablename__ = 'user_addresses'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False, comment='地址ID')

    # 防止重复关联
    __table_args__ = (
        UniqueConstraint('user_id', 'address_id', name='uq_user_address_link'),
    )

    # 可选：暴露到对象层，便于直接访问
    user = relationship('User', back_populates='user_addresses')
    address = relationship('Address', backref='user_links')
