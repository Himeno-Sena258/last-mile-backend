from __future__ import annotations

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 为了避免 app.db.database 在 import 时读取环境变量失败，这里提供默认值。
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from app.db.database import Base  # noqa: E402
import app.models  # noqa: F401,E402  # 确保模型已注册到 Base.metadata


@pytest.fixture()
def db_session(tmp_path) -> Generator[Session, None, None]:
    """创建临时 SQLite 数据库并返回一个 Session。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

