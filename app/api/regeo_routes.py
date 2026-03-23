from fastapi import APIRouter

from app.api._helpers import raise_http
from app.schemas.regeo import RegeoRequest, RegeoResponse
from app.services.errors import ServiceError
from app.services.regeo_service import regeo

router = APIRouter()


@router.post("/api/regeo", response_model=RegeoResponse)
async def regeo_endpoint(request: RegeoRequest):
    """逆地理 + 周边 POI，请求坐标为 WGS-84，响应坐标统一为 WGS-84。"""
    try:
        return regeo(request.latitude, request.longitude)
    except ServiceError as e:
        raise_http(e)
