"""逆地理 + 周边 POI 服务：请求 WGS-84，调腾讯 API（GCJ-02），响应统一转回 WGS-84。"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any, Dict, List

import requests

from app.schemas.regeo import PoiItem, RegeoResponse
from app.services.errors import ServiceError
from app.services.geocoding_service import build_tencent_sn
from app.utils.geo import gcj02_to_wgs84, wgs84_to_gcj02

# 腾讯逆地理 WebService 路径（与地理编码同域名）
TENCENT_REGEO_PATH = "/ws/geocoder/v1/"


def regeo(latitude: float, longitude: float) -> RegeoResponse:
    """
    逆地理 + 周边 POI。
    - 入参为 WGS-84，内部转 GCJ-02 调用腾讯接口；
    - 返回地址与 POI 坐标统一转为 WGS-84。
    """
    api_key = (os.getenv("TENCENT_MAP_KEY") or "").strip().strip('"').strip("'")
    sk = (os.getenv("TENCENT_MAP_SK") or "").strip().strip('"').strip("'")
    base = (os.getenv("TENCENT_BASE") or "https://apis.map.qq.com").strip().strip('"').strip("'")

    if not api_key:
        raise ServiceError(status_code=500, detail="Missing TENCENT_MAP_KEY")

    url = base.rstrip("/") + TENCENT_REGEO_PATH

    # 入参 WGS-84 -> GCJ-02 再请求腾讯
    lat_gcj, lng_gcj = wgs84_to_gcj02(float(latitude), float(longitude))
    location = f"{lat_gcj},{lng_gcj}"

    params: Dict[str, Any] = {
        "location": location,
        "key": api_key,
        "get_poi": 1,
        "poi_options": "radius=3000;page_size=20;page_index=1",
    }
    if sk:
        try:
            sn = build_tencent_sn(TENCENT_REGEO_PATH, params, sk)
            params["sn"] = sn
        except Exception:
            params.pop("sn", None)

    try:
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
    except Exception as e:
        raise ServiceError(status_code=500, detail=str(e))

    if data.get("status") != 0:
        msg = data.get("message") or "tencent regeo failed"
        raise ServiceError(status_code=502, detail=msg)

    result = data.get("result") or {}
    address = result.get("address") or result.get("formatted_addresses", {}).get("recommend") or ""

    # POI 列表：腾讯返回 GCJ-02，转 WGS-84
    pois: List[PoiItem] = []
    for p in result.get("pois") or []:
        loc = p.get("location") or {}
        lat_g = loc.get("lat")
        lng_g = loc.get("lng")
        if lat_g is not None and lng_g is not None:
            lat_w, lng_w = gcj02_to_wgs84(float(lat_g), float(lng_g))
            pois.append(
                PoiItem(
                    name=p.get("title") or p.get("name") or "",
                    address=p.get("address"),
                    latitude=Decimal(str(round(lat_w, 6))),
                    longitude=Decimal(str(round(lng_w, 6))),
                    id=p.get("id"),
                )
            )

    return RegeoResponse(address=address, pois=pois)
