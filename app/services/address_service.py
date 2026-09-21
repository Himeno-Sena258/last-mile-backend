from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_address import Address, UserAddress
from app.models.express import Express
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.errors import ServiceError
from app.core.permissions import Permission, has_permission, require_permission


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
        require_permission(current_user, Permission.ADDRESS)
        item = Address(
            address_text=payload.address_text,
            latitude=payload.latitude,
            longitude=payload.longitude,
            coord_system=payload.coord_system,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(item)
        db.flush()
        db.add(UserAddress(user_id=current_user.id, address_id=item.id))
        self._commit(db)
        db.refresh(item)
        return item

    def get_address(self, db: Session, current_user: User, address_id: int) -> Address:
        """按 ID 获取地址。"""
        require_permission(current_user, Permission.ADDRESS)
        item = self._get_or_404(db, address_id)
        if not has_permission(current_user, Permission.ADDRESS_ALL) and not self._visible_query(db, current_user).filter(Address.id == address_id).first():
            raise ServiceError(status_code=403, detail="无权限访问该地址")
        return item

    def _visible_query(self, db, current_user):
        query = db.query(Address)
        if has_permission(current_user, Permission.ADDRESS_ALL):
            return query
        own_links = db.query(UserAddress.address_id).filter(UserAddress.user_id == current_user.id)
        express_addresses = db.query(Express.recipient_address_id).filter(Express.recipient_user_id == current_user.id)
        return query.filter(Address.id.in_(own_links) | Address.id.in_(express_addresses))

    def _ensure_writable(self, db, current_user, address_id):
        require_permission(current_user, Permission.ADDRESS)
        if has_permission(current_user, Permission.ADDRESS_ALL):
            return
        owned = db.query(UserAddress).filter_by(user_id=current_user.id, address_id=address_id).first()
        shared = db.query(UserAddress).filter(UserAddress.address_id == address_id, UserAddress.user_id != current_user.id).first()
        in_delivery = db.query(Express).filter(Express.recipient_address_id == address_id).first()
        if not owned or shared or in_delivery:
            raise ServiceError(status_code=403, detail="不能修改共享或配送使用的地址")

    def list_addresses(self, db: Session, current_user: User) -> List[Address]:
        """获取地址列表。"""
        require_permission(current_user, Permission.ADDRESS)
        return self._visible_query(db, current_user).order_by(Address.id.desc()).all()

    def update_address(self, db: Session, current_user: User, address_id: int, payload: AddressUpdate) -> Address:
        """更新地址。"""
        self._ensure_writable(db, current_user, address_id)
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
        self._ensure_writable(db, current_user, address_id)
        item = self._get_or_404(db, address_id)
        if db.query(Express).filter(Express.recipient_address_id == address_id).first():
            raise ServiceError(status_code=409, detail="配送使用的地址不能删除")
        db.query(UserAddress).filter(UserAddress.address_id == address_id).delete(synchronize_session=False)
        db.delete(item)
        self._commit(db)
        return {"message": "删除成功"}
