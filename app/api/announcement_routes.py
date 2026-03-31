from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api._helpers import raise_http
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate
from app.services.announcement_service import AnnouncementService
from app.services.errors import ServiceError

router = APIRouter()
_announcement_service = AnnouncementService()


@router.post("/api/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """创建公告。"""
    try:
        return _announcement_service.create_announcement(db=db, current_user=current_user, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.get("/api/announcements", response_model=List[AnnouncementResponse])
async def list_announcements(db: Session = Depends(get_db)):
    """获取公告列表。"""
    try:
        return _announcement_service.list_announcements(db=db)
    except ServiceError as e:
        raise_http(e)


@router.get("/api/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(announcement_id: int, db: Session = Depends(get_db)):
    """获取公告详情。"""
    try:
        return _announcement_service.get_announcement(db=db, announcement_id=announcement_id)
    except ServiceError as e:
        raise_http(e)


@router.put("/api/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新公告。"""
    try:
        return _announcement_service.update_announcement(
            db=db, current_user=current_user, announcement_id=announcement_id, payload=payload
        )
    except ServiceError as e:
        raise_http(e)


@router.delete("/api/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """删除公告。"""
    try:
        return _announcement_service.delete_announcement(db=db, current_user=current_user, announcement_id=announcement_id)
    except ServiceError as e:
        raise_http(e)
