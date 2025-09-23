from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class AnnouncementBase(BaseModel):
    """公告基础schema"""
    title: str = Field(..., max_length=200, description="公告标题")
    content: str = Field(..., max_length=2000, description="公告内容")
    date: str = Field(..., max_length=50, description="公告日期")
    is_active: bool = Field(default=True, description="是否有效")
    icon: Optional[str] = Field(None, max_length=200, description="公告图标")

class AnnouncementCreate(AnnouncementBase):
    """创建公告schema"""
    pass

class AnnouncementUpdate(BaseModel):
    """更新公告schema"""
    title: Optional[str] = Field(None, max_length=200, description="公告标题")
    content: Optional[str] = Field(None, max_length=2000, description="公告内容")
    date: Optional[str] = Field(None, max_length=50, description="公告日期")
    is_active: Optional[bool] = Field(None, description="是否有效")
    icon: Optional[str] = Field(None, max_length=200, description="公告图标")

class AnnouncementResponse(AnnouncementBase):
    """公告响应schema"""
    id: int = Field(..., description="公告ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)