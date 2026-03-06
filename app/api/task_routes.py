from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api._helpers import raise_http
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.errors import ServiceError
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatusUpdate,
)
from app.services.task_service import TaskService

router = APIRouter()
_task_service = TaskService()


@router.post('/api/tasks', response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建任务（协议保持不变）。"""
    try:
        return _task_service.create_task(db=db, current_user=current_user, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/tasks/{task_id}', response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取任务详情（协议保持不变）。"""
    try:
        return _task_service.get_task(db=db, current_user=current_user, task_id=task_id)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/tasks', response_model=List[TaskResponse])
async def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出任务列表（协议保持不变）。"""
    try:
        return _task_service.list_tasks(db=db, current_user=current_user)
    except ServiceError as e:
        raise_http(e)


@router.put('/api/tasks/{task_id}', response_model=TaskResponse)
async def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新任务（协议保持不变）。"""
    try:
        return _task_service.update_task(db=db, current_user=current_user, task_id=task_id, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.patch('/api/tasks/{task_id}/status', response_model=TaskResponse)
async def update_task_status(task_id: int, payload: TaskStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新任务状态（协议保持不变）。"""
    try:
        return _task_service.update_task_status(db=db, current_user=current_user, task_id=task_id, payload=payload)
    except ServiceError as e:
        raise_http(e)