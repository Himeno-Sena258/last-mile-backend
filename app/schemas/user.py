from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.enums import UserRole

class UserBase(BaseModel):
    """用户基础schema"""
    username: str = Field(..., max_length=50, description="用户名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    name: str = Field(..., max_length=100, description="姓名")
    phone: str = Field(..., max_length=20, description="电话")
    address: Optional[List[str]] = Field(None, description="地址")
    role: UserRole = Field(default=UserRole.customer, description="用户角色")
    is_active: bool = Field(default=True, description="是否激活")

class UserCreate(UserBase):
    """创建用户schema"""
    password: str = Field(..., min_length=6, description="密码")

class UserUpdate(BaseModel):
    """更新用户schema"""
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(default=True, description="是否激活")

class UserResponse(UserBase):
    """用户响应schema"""
    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    """用户登录schema"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

