from pydantic import field_validator
from .user_base import UserBase

class UserCreate(UserBase):
    """用户创建模型"""
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码"""
        if not v or not v.strip():
            raise ValueError('密码不能为空')
        v = v.strip()
        if len(v) < 6:
            raise ValueError('密码长度不能少于6个字符')
        if len(v) > 128:
            raise ValueError('密码长度不能超过128个字符')
        return v
