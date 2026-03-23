from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, condecimal


class RegeoRequest(BaseModel):
    """逆地理 + POI 请求，坐标为 WGS-84。"""
    latitude: condecimal(max_digits=9, decimal_places=6, ge=-90, le=90) = Field(
        ..., description="纬度 (WGS-84)"
    )
    longitude: condecimal(max_digits=9, decimal_places=6, ge=-180, le=180) = Field(
        ..., description="经度 (WGS-84)"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class PoiItem(BaseModel):
    """周边 POI 项，坐标统一为 WGS-84。"""
    name: str = Field(..., description="POI 名称")
    address: Optional[str] = Field(None, description="POI 地址")
    latitude: condecimal(max_digits=9, decimal_places=6, ge=-90, le=90) = Field(
        ..., description="纬度 (WGS-84)"
    )
    longitude: condecimal(max_digits=9, decimal_places=6, ge=-180, le=180) = Field(
        ..., description="经度 (WGS-84)"
    )
    id: Optional[str] = Field(None, description="POI 唯一标识")

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class RegeoResponse(BaseModel):
    """逆地理 + POI 响应，坐标统一为 WGS-84。"""
    address: str = Field(..., description="当前中心点逆地理得到的地址")
    pois: list[PoiItem] = Field(default_factory=list, description="周边 POI 列表")
