from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api._helpers import raise_http
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.dispatch import DispatchRunResponse
from app.services.dispatch_service import DispatchService
from app.services.errors import ServiceError

router = APIRouter()
_dispatch_service = DispatchService()


@router.post("/api/dispatch/run", response_model=DispatchRunResponse)
async def run_dispatch(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员触发一次调度周期：创建任务 -> 分配空闲小车（完成回传另行由小车通知）。"""
    try:
        result = await _dispatch_service.run_dispatch_cycle(db=db, current_user=current_user)
        return result
    except ServiceError as e:
        raise_http(e)

