from __future__ import annotations

from decimal import Decimal

import pytest

from app.schemas.geocoding import GeocodeOptions
from app.schemas.regeo import PoiItem
from app.services.errors import ServiceError
from app.services.geocoding_service import geocode_tencent
from app.services.regeo_service import regeo
from app.utils.geo import gcj02_to_wgs84, wgs84_to_gcj02

from app.models.enums import GeocodingStatus


def test_geo_out_of_china_roundtrip_identity() -> None:
    # 经度/纬度不在中国范围内，函数应直接返回原值
    lat, lng = 1.0, 150.0

    gcj_lat, gcj_lng = wgs84_to_gcj02(lat, lng)
    assert gcj_lat == lat
    assert gcj_lng == lng

    wgs_lat, wgs_lng = gcj02_to_wgs84(gcj_lat, gcj_lng)
    assert wgs_lat == lat
    assert wgs_lng == lng


def test_geo_china_roundtrip_close() -> None:
    # 在中国范围内，互转后应非常接近原始坐标（允许一定误差）
    wgs_lat, wgs_lng = 39.9042, 116.4074
    gcj_lat, gcj_lng = wgs84_to_gcj02(wgs_lat, wgs_lng)
    back_lat, back_lng = gcj02_to_wgs84(gcj_lat, gcj_lng)

    # 允许 0.001 度误差（约 100m 级别），避免因算法迭代近似导致测试抖动
    assert abs(back_lat - wgs_lat) < 1e-3
    assert abs(back_lng - wgs_lng) < 1e-3


class _FakeResp:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_geocode_tencent_missing_address() -> None:
    opts = GeocodeOptions(api_key="any")
    resp = geocode_tencent("", opts)
    assert resp.geocoding_status == GeocodingStatus.failed
    assert resp.message == "address is required"
    assert resp.lat_lng is None


def test_geocode_tencent_missing_api_key() -> None:
    import os
    os.environ.pop("AMAP_KEY", None)
    opts = GeocodeOptions(api_key=None)
    resp = geocode_tencent("somewhere", opts)
    assert resp.geocoding_status == GeocodingStatus.failed
    assert resp.message == "Missing AMAP_KEY"
    assert resp.lat_lng is None


def test_geocode_tencent_success_mock_requests(monkeypatch) -> None:
    # 准备环境变量（service 里会读取）
    monkeypatch.setenv("AMAP_BASE", "https://fake.example.com")

    # mock requests.get
    def fake_get(url: str, params: dict, timeout: int):
        assert "address" in params
        assert params["key"] == "test_key"
        return _FakeResp(
            {
                "status": "1",
                "count": "1",
                "geocodes": [{"location": "121.5,31.235"}],
            }
        )

    monkeypatch.setattr("app.services.geocoding_service.requests.get", fake_get)

    opts = GeocodeOptions(api_key="test_key", sk=None)
    resp = geocode_tencent("somewhere", opts)
    assert resp.geocoding_status == GeocodingStatus.success
    assert resp.coord_system.value == "GCJ-02"
    assert resp.lat_lng is not None
    assert float(resp.lat_lng.latitude) == pytest.approx(31.235, rel=1e-9)
    assert float(resp.lat_lng.longitude) == pytest.approx(121.5, rel=1e-9)


def test_regeo_missing_api_key_raises(monkeypatch) -> None:
    monkeypatch.delenv("AMAP_KEY", raising=False)
    with pytest.raises(ServiceError) as excinfo:
        regeo(39.0, 116.0)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Missing AMAP_KEY"


def test_regeo_success_mock_requests(monkeypatch) -> None:
    monkeypatch.setenv("AMAP_KEY", "test_key")

    # mock requests.get，返回一组 pois（location 用 GCJ-02）
    def fake_get(url: str, params: dict, timeout: int):
        assert "location" in params
        assert params["key"] == "test_key"
        return _FakeResp(
            {
                "status": "1",
                "regeocode": {
                    "formatted_address": "Mock Address",
                    "pois": [
                        {
                            "name": "POI-1",
                            "address": "POI-1 Address",
                            "id": "1",
                            "location": "121.2,31.1",
                        }
                    ],
                },
            }
        )

    monkeypatch.setattr("app.services.regeo_service.requests.get", fake_get)

    wgs_lat, wgs_lng = 31.2, 121.3
    resp = regeo(wgs_lat, wgs_lng)
    assert resp.address == "Mock Address"
    assert len(resp.pois) == 1

    poi = resp.pois[0]
    assert poi.name == "POI-1"
    assert poi.address == "POI-1 Address"
    assert poi.id == "1"

    # service 会把 GCJ-02 的 pois 坐标转换回 WGS-84 并 round 到 6 位
    expected_wgs_lat, expected_wgs_lng = gcj02_to_wgs84(31.1, 121.2)
    expected_lat = Decimal(str(round(expected_wgs_lat, 6)))
    expected_lng = Decimal(str(round(expected_wgs_lng, 6)))
    assert poi.latitude == expected_lat
    assert poi.longitude == expected_lng

