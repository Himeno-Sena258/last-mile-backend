from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.core.permissions import Permission, require_permission

from app.api._helpers import raise_http
from app.schemas.geocoding import GeocodeRequest, GeocodeResponse

from app.services.errors import ServiceError
from app.services.geocoding_service import geocode_address

router = APIRouter()



@router.post("/api/geocoding", response_model=GeocodeResponse)
async def geocoding(request: GeocodeRequest, current_user=Depends(get_current_user)):
    """地理编码（协议保持不变）。"""
    try:
        require_permission(current_user, Permission.MAP)
        return geocode_address(request.address, request.opts)
    except ServiceError as e:
        raise_http(e)
