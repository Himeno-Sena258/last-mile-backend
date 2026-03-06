from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

from app.services.errors import ServiceError


def raise_http(e: ServiceError) -> NoReturn:
    """将 ServiceError 统一转换为 FastAPI HTTPException。"""
    raise HTTPException(status_code=e.status_code, detail=e.detail, headers=e.headers)

