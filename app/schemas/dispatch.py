from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DispatchRunResponse(BaseModel):
    """一次调度周期的简要结果（不包含小车回传完成事件的累计）。"""

    started_at: datetime = Field(default_factory=datetime.utcnow)
    created_task_ids: List[int] = Field(default_factory=list)
    assigned_task_ids: List[int] = Field(default_factory=list)
    dispatched_messages: int = 0
    skipped: Optional[str] = None

