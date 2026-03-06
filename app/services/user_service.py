from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.core.security import (
    authenticate_user,
    create_access_token,
    get_email,
    get_password_hash,
    get_user,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.errors import ServiceError


class UserService:
    """用户相关业务服务。

    约束：
    - 为保持现有接口协议一致，本服务抛出 `ServiceError` 并复用既有的 status_code/detail 文案；
      Controller 负责将其转换为 `HTTPException`。
    - DB 写操作按现有逻辑 commit/refresh；如需更强健的事务与回滚策略，可在后续统一增强。
    """

    def _commit(self, db: Session) -> None:
        """提交事务；失败时回滚并抛出统一 500 异常。"""
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ServiceError(status_code=500, detail="数据库操作失败")

    def register_user(self, db: Session, payload: UserCreate) -> User:
        """注册新用户并返回用户实体（用于响应序列化）。"""
        db_user = get_user(db, payload.username)
        if db_user:
            raise ServiceError(status_code=400, detail="用户已被注册")

        if payload.email:
            db_email = get_email(db, payload.email)
            if db_email:
                raise ServiceError(status_code=400, detail="邮箱已被注册")

        hashed_password = get_password_hash(payload.password)
        now = datetime.now()
        db_user = User(
            username=payload.username,
            email=payload.email,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
            role=payload.role,
            is_active=True,
            hashed_password=hashed_password,
            avatar_url=getattr(payload, "avatar_url", None),
            created_at=now,
            updated_at=now,
        )

        db.add(db_user)
        self._commit(db)
        db.refresh(db_user)
        return db_user

    def login_user(self, db: Session, username: str, password: str) -> dict:
        """校验用户名密码并签发 JWT Token（返回结构保持既有格式）。"""
        user = authenticate_user(db, username, password)
        if not user:
            raise ServiceError(status_code=401, detail="用户名或密码错误")

        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}

    def update_current_user(self, db: Session, current_user: User, payload: UserUpdate) -> User:
        """更新当前用户信息并返回更新后的用户实体。"""
        if payload.email is not None:
            existing = get_email(db, payload.email)
            if existing and existing.id != current_user.id:
                raise ServiceError(status_code=400, detail="邮箱已被注册")
            current_user.email = payload.email
        if payload.name is not None:
            current_user.name = payload.name
        if payload.phone is not None:
            current_user.phone = payload.phone
        if payload.address is not None:
            current_user.address = payload.address
        if payload.role is not None:
            current_user.role = payload.role
        if payload.is_active is not None:
            current_user.is_active = payload.is_active
        if getattr(payload, "avatar_url", None) is not None:
            current_user.avatar_url = payload.avatar_url

        current_user.updated_at = datetime.now()
        db.add(current_user)
        self._commit(db)
        db.refresh(current_user)
        return current_user

    def get_user_by_id(self, db: Session, current_user: User, user_id: int) -> User:
        """按 ID 获取用户，并按现有权限规则进行访问控制。"""
        user_obj = db.query(User).filter(User.id == user_id).first()
        if not user_obj:
            raise ServiceError(status_code=404, detail="用户不存在")
        if current_user.role != UserRole.admin and current_user.id != user_id:
            raise ServiceError(status_code=403, detail="无权限访问")
        return user_obj

    def list_users(self, db: Session, current_user: User) -> List[User]:
        """列出全部用户（仅管理员可访问）。"""
        if current_user.role != UserRole.admin:
            raise ServiceError(status_code=403, detail="无权限访问")
        return db.query(User).all()
