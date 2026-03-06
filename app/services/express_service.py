from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.express import Express
from app.models.user import User
from app.models.user_address import Address
from app.schemas.express import ExpressCreate, ExpressStatusUpdate, ExpressUpdate
from app.services.errors import ServiceError


class ExpressService:
    """快递相关业务服务。"""

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def _ensure_access(self, express_item: Express, current_user: User) -> None:
        """确保当前用户可访问指定快递。"""
        if current_user.role != UserRole.admin and express_item.recipient_user_id != current_user.id:
            raise ServiceError(status_code=403, detail="无权限访问该快递")

    def _get_or_404(self, db: Session, express_id: int) -> Express:
        """获取快递，不存在则抛出 404。"""
        item = db.query(Express).filter(Express.id == express_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="快递不存在")
        return item

    def _create_address(self, db: Session, address_text: str) -> Address:
        """创建地址实体并返回。"""
        addr = Address(address_text=address_text, created_at=datetime.now(), updated_at=datetime.now())
        db.add(addr)
        self._commit(db)
        db.refresh(addr)
        return addr

    def create_express(self, db: Session, current_user: User, payload: ExpressCreate) -> Express:
        """创建快递。"""
        if current_user.role != UserRole.admin and payload.recipient_user_id != current_user.id:
            raise ServiceError(status_code=403, detail="只能为自己创建快递")

        exists = db.query(Express).filter(Express.tracking_number == payload.tracking_number).first()
        if exists:
            raise ServiceError(status_code=400, detail="快递单号已存在")

        addr = self._create_address(db, payload.recipient_address)

        new_item = Express(
            recipient_name=payload.recipient_name,
            recipient_phone=payload.recipient_phone,
            recipient_address_id=addr.id,
            tracking_number=payload.tracking_number,
            recipient_user_id=payload.recipient_user_id,
            status=payload.status,
            task_id=payload.task_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(new_item)
        self._commit(db)
        db.refresh(new_item)
        return new_item

    def get_express(self, db: Session, current_user: User, express_id: int) -> Express:
        """获取快递详情。"""
        item = self._get_or_404(db, express_id)
        self._ensure_access(item, current_user)
        return item

    def list_express(self, db: Session, current_user: User) -> List[Express]:
        """列出快递列表。"""
        if current_user.role == UserRole.admin:
            return db.query(Express).all()
        return db.query(Express).filter(Express.recipient_user_id == current_user.id).all()

    def update_express(self, db: Session, current_user: User, express_id: int, payload: ExpressUpdate) -> Express:
        """更新快递字段。"""
        item = self._get_or_404(db, express_id)
        self._ensure_access(item, current_user)

        if payload.recipient_name is not None:
            item.recipient_name = payload.recipient_name
        if payload.recipient_phone is not None:
            item.recipient_phone = payload.recipient_phone
        if payload.recipient_address is not None:
            addr = self._create_address(db, payload.recipient_address)
            item.recipient_address_id = addr.id
        if payload.status is not None:
            item.status = payload.status
        if payload.task_id is not None:
            item.task_id = payload.task_id

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def update_express_status(self, db: Session, current_user: User, express_id: int, payload: ExpressStatusUpdate) -> Express:
        """更新快递状态。"""
        item = self._get_or_404(db, express_id)
        self._ensure_access(item, current_user)

        item.status = payload.status
        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

