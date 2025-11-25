from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserSession(BaseModel):
    """用户会话模型：跟踪用户设备登录会话状态

    - 使用统一的 BaseModel 提供 `id/created_at/updated_at`
    - `session_id` 保存业务会话ID（UUID），作为唯一键供路由和服务层使用
    """
    __tablename__ = 'user_sessions'

    session_id = Column(String(255), unique=True, index=True, nullable=False, comment='业务会话ID(UUID)')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    device_id = Column(String(255), nullable=False, comment='设备ID')
    start_time = Column(DateTime, nullable=False, comment='会话开始时间')
    last_active_time = Column(DateTime, nullable=False, comment='会话最后活跃时间')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    expires_at = Column(DateTime, nullable=False, comment='会话过期时间')

    user = relationship('User', back_populates='sessions')
