from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

from app.schemas.geocoding import (
    GeocodeOptions,
    GeocodeResponse,
    LatLng,
    CoordSystem,
)
from app.models.enums import GeocodingStatus


def build_tencent_sn(path: str, params: Dict[str, Any], sk: str) -> str:
    """生成腾讯地图 WebService API 的 SN 签名。

    步骤：
    1) 将 URL 路径（不含域名）与所有参数按键名 ASCII 升序排序；
    2) 参数值使用 URL 编码（空格使用 %20）；
    3) 拼接成字符串："{path}?key1=val1&key2=val2"；
    4) 将该字符串与 SK 直接拼接："{path}?...{sk}"；
    5) 对最终拼接字符串进行 URL 编码后计算 MD5，得到 SN。
    """
    if not sk:
        raise ValueError("Tencent SK is required to build SN")

    sorted_items = sorted(params.items())
    query = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in sorted_items)
    raw = f"{path}?{query}{sk}"
    encoded = quote(raw, safe="")
    return hashlib.md5(encoded.encode("utf-8")).hexdigest()


def geocode_tencent(address: str, opts: GeocodeOptions) -> GeocodeResponse:
    """调用腾讯地图地理编码服务并返回统一响应结构。

    - 必填：address（仅使用腾讯实现）
    - API Key 优先使用 opts.api_key；否则读取环境变量 TENCENT_MAP_KEY
    - Secret Key(SK) 优先使用 opts.sk；否则读取环境变量 TENCENT_MAP_SK
    """
    if not address:
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message="address is required",
            geocoded_at=datetime.utcnow(),
        )

    api_key = (opts.api_key or os.getenv("TENCENT_MAP_KEY") or "").strip().strip('"').strip("'")
    sk = (opts.sk or os.getenv("TENCENT_MAP_SK") or "").strip().strip('"').strip("'")
    region = opts.region

    if not api_key:
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message="Missing TENCENT_MAP_KEY",
            geocoded_at=datetime.utcnow(),
        )

    base = (os.getenv("TENCENT_BASE") or "").strip().strip('"').strip("'")
    path = (os.getenv("TENCENT_GEOCODER_PATH") or "").strip().strip('"').strip("'")
    if not base or not path:
        return GeocodeResponse(
            lat_lng=None,
            geocoding_status=GeocodingStatus.failed,
            message="Missing TENCENT_BASE or TENCENT_GEOCODER_PATH",
            geocoded_at=datetime.utcnow(),
        )
    # 规范化URL拼接
    path = path if path.startswith("/") else f"/{path}"
    url = base.rstrip("/") + path

    params: Dict[str, Any] = {"address": address, "key": api_key}
    if region:
        params["region"] = region

    try:
        # 当存在SK时计算SN签名；否则直接请求（腾讯支持仅Key访问）
        if sk:
            try:
                sn = build_tencent_sn(path, params, sk)
                params["sn"] = sn
            except Exception:
                # SN生成失败时先移除签名，走无签名兜底
                params.pop("sn", None)

        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()

        # 如果签名失败且存在SK，尝试一次不带签名的兜底请求
        if data.get("status") != 0 and sk and ("sign" in (data.get("message") or "").lower() or "sn" in (data.get("message") or "").lower()):
            params.pop("sn", None)
            resp = requests.get(url, params=params, timeout=8)
            data = resp.json()

        if data.get("status") == 0 and data.get("result", {}).get("location"):
            loc = data["result"]["location"]
            latlng = LatLng(latitude=loc["lat"], longitude=loc["lng"])
            return GeocodeResponse(
                lat_lng=latlng,
                coord_system=CoordSystem.GCJ02,
                geocoding_status=GeocodingStatus.success,
                geocoded_at=datetime.utcnow(),
            )

        message = data.get("message") or "tencent geocoder failed"
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