from fastapi import APIRouter

from app.api._helpers import raise_http
from app.schemas.geocoding import GeocodeRequest, GeocodeResponse

from app.services.errors import ServiceError
from app.services.geocoding_service import geocode_address

router = APIRouter()



@router.post("/api/geocoding", response_model=GeocodeResponse)
async def geocoding(request: GeocodeRequest):
    """地理编码（协议保持不变）。"""
    try:
        return geocode_address(request.address, request.opts)
    except ServiceError as e:
        raise_http(e)
