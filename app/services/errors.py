from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True, slots=True)
class ServiceError(Exception):
    """Service 层业务异常。

    设计目标：
    - Service 层抛出结构化异常；
    - Controller 层捕获后统一转换为 `HTTPException`；
    - 保持既有接口协议（status_code 与 detail 文案）不变。
    """

    status_code: int
    detail: str
    headers: Optional[Mapping[str, str]] = None
    extra: Optional[Mapping[str, Any]] = None

