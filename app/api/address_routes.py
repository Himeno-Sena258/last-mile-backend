from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api._helpers import raise_http
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.services.address_service import AddressService
from app.services.errors import ServiceError

router = APIRouter()
_address_service = AddressService()


@router.post("/api/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: AddressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """创建地址。"""
    try:
        return _address_service.create_address(db=db, current_user=current_user, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.get("/api/addresses", response_model=List[AddressResponse])
async def list_addresses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取地址列表。"""
    try:
        return _address_service.list_addresses(db=db, current_user=current_user)
    except ServiceError as e:
        raise_http(e)


@router.get("/api/addresses/{address_id}", response_model=AddressResponse)
async def get_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取地址详情。"""
    try:
        return _address_service.get_address(db=db, current_user=current_user, address_id=address_id)
    except ServiceError as e:
        raise_http(e)


@router.put("/api/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: int,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新地址。"""
    try:
        return _address_service.update_address(db=db, current_user=current_user, address_id=address_id, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.delete("/api/addresses/{address_id}")
async def delete_address(
    address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """删除地址。"""
    try:
        return _address_service.delete_address(db=db, current_user=current_user, address_id=address_id)
    except ServiceError as e:
        raise_http(e)
