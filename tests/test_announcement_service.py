from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from app.services.announcement_service import AnnouncementService
from app.services.errors import ServiceError


def _create_user(db: Session, *, username: str, role: UserRole) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hash",
        name=username,
        phone="13800000000",
        address=None,
        role=role,
        is_active=True,
        avatar_url=None,
    )
    db.add(user)
    db.flush()
    return user


def test_create_and_list_announcements(db_session: Session):
    db = db_session
    admin = _create_user(db, username="admin_anno", role=UserRole.admin)
    service = AnnouncementService()

    created = service.create_announcement(
        db=db,
        current_user=admin,
        payload=AnnouncementCreate(
            title="系统通知",
            content="本周有系统维护",
            date="2026-03-31",
            is_active=True,
            icon="AlertCircle",
        ),
    )

    assert created.id is not None
    assert created.title == "系统通知"

    items = service.list_announcements(db)
    assert len(items) == 1
    assert items[0].id == created.id


def test_update_announcement(db_session: Session):
    db = db_session
    admin = _create_user(db, username="admin_anno2", role=UserRole.admin)
    service = AnnouncementService()

    base = Announcement(title="T1", content="C1", date="2026-03-31", is_active=True, icon="Info")
    db.add(base)
    db.commit()
    db.refresh(base)

    updated = service.update_announcement(
        db=db,
        current_user=admin,
        announcement_id=base.id,
        payload=AnnouncementUpdate(title="T2", is_active=False),
    )

    assert updated.title == "T2"
    assert updated.is_active is False


def test_delete_announcement(db_session: Session):
    db = db_session
    admin = _create_user(db, username="admin_anno3", role=UserRole.admin)
    service = AnnouncementService()

    base = Announcement(title="T", content="C", date="2026-03-31", is_active=True, icon=None)
    db.add(base)
    db.commit()
    db.refresh(base)

    result = service.delete_announcement(db=db, current_user=admin, announcement_id=base.id)
    assert result["message"] == "删除成功"
    assert service.list_announcements(db) == []


def test_non_admin_cannot_write_announcements(db_session: Session):
    db = db_session
    user = _create_user(db, username="customer_anno", role=UserRole.customer)
    service = AnnouncementService()

    try:
        service.create_announcement(
            db=db,
            current_user=user,
            payload=AnnouncementCreate(
                title="系统通知",
                content="本周有系统维护",
                date="2026-03-31",
                is_active=True,
                icon=None,
            ),
        )
        assert False, "expected ServiceError"
    except ServiceError as e:
        assert e.status_code == 403
