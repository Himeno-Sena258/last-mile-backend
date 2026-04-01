from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AddressBase(BaseModel):
    """地址基础 Schema。"""

    address_text: str = Field(..., description="地址字符串")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    coord_system: str = Field(default="WGS84", max_length=10, description="坐标系统")


class AddressCreate(AddressBase):
    """创建地址 Schema。"""


class AddressUpdate(BaseModel):
    """更新地址 Schema。"""

    address_text: Optional[str] = Field(None, description="地址字符串")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    coord_system: Optional[str] = Field(None, max_length=10, description="坐标系统")


class AddressResponse(AddressBase):
    """地址响应 Schema。"""

    id: int = Field(..., description="地址ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)
