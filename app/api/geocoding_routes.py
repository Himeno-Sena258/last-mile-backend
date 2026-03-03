from fastapi import APIRouter, Depends, HTTPException
from app.schemas.geocoding import GeocodingRequest, GeocodingResponse, GeocodeOptions

from app.services.geocoding_service import geocode_tencent

router = APIRouter()



@router.post("/api/geocoding", response_model=GeocodingResponse)
async def geocoding(request: GeocodingRequest):
    try:
        return await geocode_tencent(request.address, request.opts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
