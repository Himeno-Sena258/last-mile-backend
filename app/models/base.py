from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime
from app.db.database import Base

class BaseModel(Base):
    """所有模型的基础类，包含通用字段"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, comment='主键ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')