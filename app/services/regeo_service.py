"""逆地理 + 周边 POI 服务：请求 WGS-84，调高德 API（GCJ-02），响应统一转回 WGS-84。"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any, Dict, List

import requests

from app.schemas.regeo import PoiItem, RegeoResponse
from app.services.errors import ServiceError
from app.utils.geo import gcj02_to_wgs84, wgs84_to_gcj02

# 高德逆地理 WebService 路径
AMAP_REGEO_PATH = "/v3/geocode/regeo"


def regeo(latitude: float, longitude: float) -> RegeoResponse:
    """
    逆地理 + 周边 POI。
    - 入参为 WGS-84，内部转 GCJ-02 调用高德接口；
    - 返回地址与 POI 坐标统一转为 WGS-84。
    """
    api_key = (os.getenv("AMAP_KEY") or "").strip().strip('"').strip("'")
    base = (os.getenv("AMAP_BASE") or "https://restapi.amap.com").strip().strip('"').strip("'")

    if not api_key:
        raise ServiceError(status_code=500, detail="Missing AMAP_KEY")

    url = base.rstrip("/") + AMAP_REGEO_PATH

    # 入参 WGS-84 -> GCJ-02 再请求高德
    lat_gcj, lng_gcj = wgs84_to_gcj02(float(latitude), float(longitude))
    location = f"{lng_gcj},{lat_gcj}"

    params: Dict[str, Any] = {
        "location": location,
        "key": api_key,
        "extensions": "all",
        "radius": 3000,
        "roadlevel": 0,
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
    except Exception as e:
        raise ServiceError(status_code=500, detail=str(e))

    if data.get("status") != "1":
        msg = data.get("info") or "amap regeo failed"
        raise ServiceError(status_code=502, detail=msg)

    result = data.get("regeocode") or {}
    address = result.get("formatted_address") or ""

    # POI 列表：高德返回 GCJ-02，转 WGS-84
    pois: List[PoiItem] = []
    for p in result.get("pois") or []:
        loc = p.get("location")
        if not loc:
            continue
        lng_lat = str(loc).split(",")
        if len(lng_lat) == 2:
            lng_g = float(lng_lat[0])
            lat_g = float(lng_lat[1])
            lat_w, lng_w = gcj02_to_wgs84(float(lat_g), float(lng_g))
            pois.append(
                PoiItem(
                    name=p.get("name") or "",
                    address=p.get("address"),
                    latitude=Decimal(str(round(lat_w, 6))),
                    longitude=Decimal(str(round(lng_w, 6))),
                    id=p.get("id"),
                )
            )

    return RegeoResponse(address=address, pois=pois)
