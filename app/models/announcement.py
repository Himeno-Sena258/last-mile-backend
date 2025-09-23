from sqlalchemy import Column, Integer, String, Enum, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Announcement(BaseModel):
    __tablename__ = 'announcements'

    title = Column(String(200), nullable=False, comment='公告标题')
    content = Column(String(2000), nullable=False, comment='公告内容')
    date = Column(String(50), nullable=False, comment='公告日期')
    is_active = Column(Boolean, default=True, comment='是否有效')
    icon = Column(String(200), nullable=True, comment='公告图标')