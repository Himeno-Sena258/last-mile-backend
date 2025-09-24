from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import ForeignKey
from datetime import datetime

base = declarative_base()

class UserSession(base):
    __tablename__ = 'user_sessions'
    session_id = Column(String(255), primary_key=True, comment='会话ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    device_id = Column(String(255), nullable = False, comment = '设备id')
    start_time = Column(DateTime, nullable = False, comment='会话开始时间')
    last_active_time = Column(DateTime, nullable = False, comment='会话最后活跃时间')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    expires_at = Column(DateTime, nullable = False, comment='会话过期时间')
    user = relationship('User', back_populates='sessions')
