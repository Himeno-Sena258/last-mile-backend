from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
from app.models.enums import UserRole
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    username = Column(String(50), unique=True, index=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, index=True, nullable=True, comment='邮箱')
    hashed_password = Column(String(255), nullable=False, comment='加密密码')
    name = Column(String(100), nullable=False, comment='姓名')
    phone = Column(String(20), nullable=True, comment='电话')
    role = Column(Enum(UserRole), default=UserRole.customer, comment='用户类别')
    is_active = Column(Boolean, default=True, comment='是否激活')
    avatar_url = Column(String(512), nullable=True, comment='头像URL')

    appointments = relationship('Appointment', back_populates='customer')
    express_items = relationship('Express', back_populates='recipient_user', foreign_keys='Express.recipient_user_id')
    # 多对多地址关系：通过关联表 user_addresses 连接到 Address
    addresses = relationship('Address', secondary='user_addresses', back_populates='users')
    # 关联对象关系：可用于精细控制关联记录（可选）
    user_addresses = relationship('UserAddress', back_populates='user', cascade='all, delete-orphan')
    tasks = relationship('Task', back_populates='user', foreign_keys='Task.user_id')
