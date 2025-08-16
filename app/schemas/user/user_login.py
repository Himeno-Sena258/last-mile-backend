from pydantic import EmailStr, field_validator, model_validator
from typing import Optional
from app.schemas.base import BaseSchema


class UserLogin(BaseSchema):
    """用户登录模型"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str
    
    @model_validator(mode='after')
    def validate_login_fields(self) -> 'UserLogin':
        """验证登录字段：用户名和邮箱至少提供一个"""
        if not self.username and not self.email:
            raise ValueError('用户名和邮箱至少需要提供一个')
        return self
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """验证用户名"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('用户名不能为空')
            if len(v) < 3 or len(v) > 50:
                raise ValueError('用户名长度必须在3-50个字符之间')
            return v
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码"""
        if not v or not v.strip():
            raise ValueError('密码不能为空')
        return v.strip()

