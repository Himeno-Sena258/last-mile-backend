from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal

from app.models.enums import GeocodingStatus


class CoordSystem(str, Enum):
    WGS84 = "WGS84"
    GCJ02 = "GCJ-02"


class LatLng(BaseModel):
    latitude: condecimal(max_digits=9, decimal_places=6, ge=-90, le=90) = Field(
        ..., description="纬度 (WGS84/GCJ-02)", example=31.235000
    )
    longitude: condecimal(max_digits=9, decimal_places=6, ge=-180, le=180) = Field(
        ..., description="经度 (WGS84/GCJ-02)", example=121.500000
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class GeocodeOptions(BaseModel):
    api_key: Optional[str] = Field(
        None, alias="apiKey", max_length=128, description="服务商 API Key"
    )
    sk: Optional[str] = Field(
        None, alias="sk", max_length=128, description="腾讯地图签名Secret Key"
    )
    region: Optional[str] = Field(None, description="区域参数，如 Google 的 region")

    # Pydantic v2：允许用字段名而不是 alias（例如 api_key 而不是 apiKey）
    model_config = ConfigDict(populate_by_name=True)


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1, max_length=512, description="地址字符串")
    opts: GeocodeOptions = Field(..., alias="opts", description="地理编码选项")

    model_config = ConfigDict(populate_by_name=True)


class GeocodeResponse(BaseModel):
    lat_lng: Optional[LatLng] = Field(None, alias="latLng", description="坐标结果")
    coord_system: Optional[CoordSystem] = Field(
        None, alias="coordSystem", description="坐标系（默认 WGS84）"
    )
    place_id: Optional[str] = Field(None, alias="placeId", max_length=64, description="服务商 place_id")
    accuracy_m: Optional[int] = Field(None, alias="accuracyM", ge=0, description="定位精度（米）")
    geocoding_status: GeocodingStatus = Field(
        GeocodingStatus.pending, alias="geocodingStatus", description="地理编码状态"
    )
    geocoded_at: Optional[datetime] = Field(None, alias="geocodedAt", description="地理编码时间")
    message: Optional[str] = Field(None, description="错误或提示信息")

    model_config = ConfigDict(populate_by_name=True)