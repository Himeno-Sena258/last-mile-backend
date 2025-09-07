from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.models.enums import UserRole
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    username = Column(String(50), unique=True, index=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, index=True, nullable=True, comment='邮箱')
    hashed_password = Column(String(255), nullable=False, comment='加密密码')
    name = Column(String(100), nullable=False, comment='姓名')
    phone = Column(String(20), nullable=False, comment='电话')
    address = Column(String(500), nullable=True, comment='地址')
    role = Column(UserRole, default=UserRole.customer, comment='用户类别')
    is_active = Column(Boolean, default=True, comment='是否激活')

    appointments = relationship('Appointment', back_populates='customer')
    express_items = relationship('Express', back_populates='recipient_user', foreign_keys='Express.recipient_user_id')
