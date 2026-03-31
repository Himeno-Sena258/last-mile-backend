from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from app.services.errors import ServiceError


class AnnouncementService:
    """公告相关业务服务。"""

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def _ensure_admin(self, current_user: User) -> None:
        """仅允许管理员写入公告。"""
        if current_user.role != UserRole.admin:
            raise ServiceError(status_code=403, detail="无权限操作公告")

    def _get_or_404(self, db: Session, announcement_id: int) -> Announcement:
        """获取公告，不存在则抛出 404。"""
        item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="公告不存在")
        return item

    def create_announcement(self, db: Session, current_user: User, payload: AnnouncementCreate) -> Announcement:
        """创建公告。"""
        self._ensure_admin(current_user)
        item = Announcement(
            title=payload.title,
            content=payload.content,
            date=payload.date,
            is_active=payload.is_active,
            icon=payload.icon,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def get_announcement(self, db: Session, announcement_id: int) -> Announcement:
        """按 ID 获取公告。"""
        return self._get_or_404(db, announcement_id)

    def list_announcements(self, db: Session) -> List[Announcement]:
        """获取全部公告（按最新在前）。"""
        return db.query(Announcement).order_by(Announcement.id.desc()).all()

    def update_announcement(
        self,
        db: Session,
        current_user: User,
        announcement_id: int,
        payload: AnnouncementUpdate,
    ) -> Announcement:
        """更新公告。"""
        self._ensure_admin(current_user)
        item = self._get_or_404(db, announcement_id)

        if payload.title is not None:
            item.title = payload.title
        if payload.content is not None:
            item.content = payload.content
        if payload.date is not None:
            item.date = payload.date
        if payload.is_active is not None:
            item.is_active = payload.is_active
        if payload.icon is not None:
            item.icon = payload.icon

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def delete_announcement(self, db: Session, current_user: User, announcement_id: int) -> dict:
        """删除公告。"""
        self._ensure_admin(current_user)
        item = self._get_or_404(db, announcement_id)
        db.delete(item)
        self._commit(db)
        return {"message": "删除成功"}
