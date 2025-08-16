from datetime import datetime
from typing import Optional
from pydantic import EmailStr, computed_field
from app.schemas.base import BaseSchema
from app.models.enums import UserRole

class UserResponse(BaseSchema):
    """用户响应模型"""
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
    
    class Config:
        from_attributes = True

