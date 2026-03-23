# 坐标系转换：WGS-84 与 GCJ-02（腾讯/高德）互转，不依赖第三方库。

from __future__ import annotations

import math
from typing import Tuple


def _out_of_china(lat: float, lng: float) -> bool:
    return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)


def _transform_lat(lng: float, lat: float) -> float:
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat
    ret += 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 * math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * math.pi) + 40.0 * math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    return ret


def _transform_lng(lng: float, lat: float) -> float:
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng
    ret += 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 * math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * math.pi) + 40.0 * math.sin(lng / 3.0 * math.pi)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(latitude: float, longitude: float) -> Tuple[float, float]:
    """WGS-84 转 GCJ-02（火星坐标）。国外坐标原样返回。"""
    if _out_of_china(latitude, longitude):
        return (latitude, longitude)
    a, f = 6378245.0, 1 / 298.3
    ee = 2 * f - f * f
    dlat = _transform_lat(longitude - 105.0, latitude - 35.0)
    dlng = _transform_lng(longitude - 105.0, latitude - 35.0)
    radlat = latitude / 180.0 * math.pi
    magic = 1 - ee * math.sin(radlat) ** 2
    dlat = (dlat * 180.0) / (a * (1 - ee) / (magic * math.sqrt(magic)) * math.pi)
    dlng = (dlng * 180.0) / (a * math.cos(radlat) / math.sqrt(magic) * math.pi)
    return (latitude + dlat, longitude + dlng)


def gcj02_to_wgs84(latitude: float, longitude: float) -> Tuple[float, float]:
    """GCJ-02 转 WGS-84。迭代一次近似，国外坐标原样返回。"""
    if _out_of_china(latitude, longitude):
        return (latitude, longitude)
    glat, glng = wgs84_to_gcj02(latitude, longitude)
    return (latitude * 2 - glat, longitude * 2 - glng)
