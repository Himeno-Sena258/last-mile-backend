from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field, field_validator, model_validator, computed_field
from app.schemas.base import BaseSchema
from app.models.enums import UserRole
from app.schemas.validators import create_validator, validate_non_empty_string, validate_string_length, validate_pattern
from app.core.constants import MAX_LENGTHS, MIN_LENGTHS, FIELD_DESCRIPTIONS


class UserBase(BaseSchema):
    """用户基础模型
    
    包含用户的基本信息字段和验证方法
    """
    username: str = Field(
        description=FIELD_DESCRIPTIONS["username"],
        min_length=MIN_LENGTHS["username"],
        max_length=MAX_LENGTHS["username"]
    )
    email: Optional[EmailStr] = Field(None, description=FIELD_DESCRIPTIONS["email"])
    name: str = Field(description=FIELD_DESCRIPTIONS["name"], max_length=MAX_LENGTHS["name"])
    phone: str = Field(description=FIELD_DESCRIPTIONS["phone"], max_length=MAX_LENGTHS["phone"])
    address: Optional[str] = Field(None, description=FIELD_DESCRIPTIONS["address"], max_length=MAX_LENGTHS["address"])
    role: UserRole = Field(default=UserRole.customer, description=FIELD_DESCRIPTIONS["role"])
    
    # 验证用户名
    validate_username = create_validator(
        validate_non_empty_string,
        field_name="用户名"
    )
    
    # 验证姓名
    validate_name = create_validator(
        validate_non_empty_string,
        field_name="姓名"
    )
    
    # 验证电话号码
    validate_phone = create_validator(
        validate_pattern,
        pattern="phone",
        field_name="电话号码"
    )
    
    # 验证地址
    validate_address = create_validator(
        validate_string_length,
        max_length=MAX_LENGTHS["address"],
        field_name="地址"
    )


class UserCreate(UserBase):
    """用户创建模型
    
    继承自UserBase，添加密码字段和验证
    """
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


class UserUpdate(BaseSchema):
    """用户更新模型
    
    所有字段都是可选的，只更新提供的字段
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserLogin(BaseSchema):
    """用户登录模型
    
    支持使用用户名或邮箱登录
    """
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


class UserResponse(BaseSchema):
    """用户响应模型
    
    用于API返回用户信息，包含计算属性
    """
    id: int
    username: str
    email: Optional[EmailStr] = None
    name: str
    phone: str
    address: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # 关联信息字段
    @computed_field
    @property
    def appointment_count(self) -> int:
        """预约数量"""
        return getattr(self, '_appointment_count', 0)
    
    @computed_field
    @property
    def express_count(self) -> int:
        """快递数量"""
        return getattr(self, '_express_count', 0)
    
    @computed_field
    @property
    def role_display(self) -> str:
        """角色显示名称"""
        role_map = {
            UserRole.admin: '管理员',
            UserRole.customer: '客户',
            UserRole.others: '其他'
        }
        return role_map.get(self.role, '未知')
    
    @computed_field
    @property
    def status_display(self) -> str:
        """状态显示名称"""
        return '激活' if self.is_active else '禁用'