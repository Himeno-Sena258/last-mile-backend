from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

import requests

from app.schemas.geocoding import (
    GeocodeOptions,
    GeocodeResponse,
    LatLng,
    CoordSystem,
)
from app.models.enums import GeocodingStatus
from app.services.errors import ServiceError


def geocode_amap(address: str, opts: GeocodeOptions) -> GeocodeResponse:
    """调用高德地图地理编码服务并返回统一响应结构。"""
    if not address:
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message="address is required",
            geocoded_at=datetime.utcnow(),
        )

    api_key = (opts.api_key or os.getenv("AMAP_KEY") or "").strip().strip('"').strip("'")
    region = opts.region

    if not api_key:
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message="Missing AMAP_KEY",
            geocoded_at=datetime.utcnow(),
        )

    base = (os.getenv("AMAP_BASE") or "https://restapi.amap.com").strip().strip('"').strip("'")
    path = "/v3/geocode/geo"
    url = base.rstrip("/") + path

    params: Dict[str, Any] = {"address": address, "key": api_key}
    if region:
        params["city"] = region

    try:
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if data.get("status") == "1" and data.get("count") not in (None, "0"):
            geocodes = data.get("geocodes") or []
            location = (geocodes[0] or {}).get("location") if geocodes else None
            if location:
                lng_str, lat_str = location.split(",")
                latlng = LatLng(latitude=float(lat_str), longitude=float(lng_str))
            else:
                latlng = None
            if latlng is not None:
                return GeocodeResponse(
                    lat_lng=latlng,
                    coord_system=CoordSystem.GCJ02,
                    geocoding_status=GeocodingStatus.success,
                    geocoded_at=datetime.utcnow(),
                )

        message = data.get("info") or "amap geocoder failed"
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message=message,
            geocoded_at=datetime.utcnow(),
        )
    except Exception as exc:
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message=str(exc),
            geocoded_at=datetime.utcnow(),
        )


def geocode_tencent(address: str, opts: GeocodeOptions) -> GeocodeResponse:
    """兼容旧命名，内部改为调用高德。"""
    return geocode_amap(address, opts)


def geocode_address(address: str, opts: GeocodeOptions) -> GeocodeResponse:
    """应用层地理编码入口。

    - 保持响应结构由高德实现统一返回；
    - 若出现未预期异常，则抛出 `ServiceError` 供 Controller 统一映射为 500。
    """
    try:
        return geocode_amap(address, opts)
    except Exception as exc:
        raise ServiceError(status_code=500, detail=str(exc))