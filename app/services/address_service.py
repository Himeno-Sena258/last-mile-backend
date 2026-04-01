from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_address import Address
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.errors import ServiceError


class AddressService:
    """地址相关业务服务。"""

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def _get_or_404(self, db: Session, address_id: int) -> Address:
        """获取地址，不存在则抛出 404。"""
        item = db.query(Address).filter(Address.id == address_id).first()
        if not item:
            raise ServiceError(status_code=404, detail="地址不存在")
        return item

    def create_address(self, db: Session, current_user: User, payload: AddressCreate) -> Address:
        """创建地址。"""
        _ = current_user
        item = Address(
            address_text=payload.address_text,
            latitude=payload.latitude,
            longitude=payload.longitude,
            coord_system=payload.coord_system,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def get_address(self, db: Session, current_user: User, address_id: int) -> Address:
        """按 ID 获取地址。"""
        _ = current_user
        return self._get_or_404(db, address_id)

    def list_addresses(self, db: Session, current_user: User) -> List[Address]:
        """获取地址列表。"""
        _ = current_user
        return db.query(Address).order_by(Address.id.desc()).all()

    def update_address(self, db: Session, current_user: User, address_id: int, payload: AddressUpdate) -> Address:
        """更新地址。"""
        _ = current_user
        item = self._get_or_404(db, address_id)

        if payload.address_text is not None:
            item.address_text = payload.address_text
        if payload.latitude is not None:
            item.latitude = payload.latitude
        if payload.longitude is not None:
            item.longitude = payload.longitude
        if payload.coord_system is not None:
            item.coord_system = payload.coord_system

        item.updated_at = datetime.now()
        db.add(item)
        self._commit(db)
        db.refresh(item)
        return item

    def delete_address(self, db: Session, current_user: User, address_id: int) -> dict:
        """删除地址。"""
        _ = current_user
        item = self._get_or_404(db, address_id)
        db.delete(item)
        self._commit(db)
        return {"message": "删除成功"}
