from app.schemas.base import BaseSchema
from pydantic import EmailStr, field_validator
from typing import Optional
from app.models.enums import UserRole


class UserBase(BaseSchema):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    name: str
    phone: str
    address: Optional[str] = None
    role: UserRole = UserRole.customer
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名"""
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证姓名"""
        if not v or not v.strip():
            raise ValueError('姓名不能为空')
        v = v.strip()
        if len(v) > 100:
            raise ValueError('姓名长度不能超过100个字符')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证电话号码"""
        if not v or not v.strip():
            raise ValueError('电话号码不能为空')
        v = v.strip()
        if len(v) > 20:
            raise ValueError('电话号码长度不能超过20个字符')
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        """验证地址"""
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('地址长度不能超过500个字符')
            return v if v else None
        return v
