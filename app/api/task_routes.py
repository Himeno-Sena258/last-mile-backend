from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.models.task import Task
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatusUpdate,
)

router = APIRouter()


def _ensure_access(task: Task, current_user: User):
    if current_user.role != UserRole.admin and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该任务")


@router.post('/api/tasks', response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 任务创建统一归属当前用户
    new_item = Task(
        status=payload.status,
        assigned_car_number=payload.assigned_car_number,
        user_id=current_user.id,
        target_address=payload.target_address,
        target_latitude=payload.target_latitude,
        target_longitude=payload.target_longitude,
        coord_system=str(payload.coord_system),
        geocoder_place_id=payload.geocoder_place_id,
        geocoder_accuracy_m=payload.geocoder_accuracy_m,
        geocoding_status=payload.geocoding_status,
        geocoded_at=payload.geocoded_at,
        expected_completion_time=payload.expected_completion_time,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get('/api/tasks/{task_id}', response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Task).filter(Task.id == task_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    _ensure_access(item, current_user)
    return item


@router.get('/api/tasks', response_model=List[TaskResponse])
async def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.admin:
        items = db.query(Task).all()
    else:
        items = db.query(Task).filter(Task.user_id == current_user.id).all()
    return items


@router.put('/api/tasks/{task_id}', response_model=TaskResponse)
async def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Task).filter(Task.id == task_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    _ensure_access(item, current_user)

    if payload.status is not None:
        item.status = payload.status
    if payload.assigned_car_number is not None:
        item.assigned_car_number = payload.assigned_car_number
    if payload.expected_completion_time is not None:
        item.expected_completion_time = payload.expected_completion_time
    if payload.completed_at is not None:
        item.completed_at = payload.completed_at
    if payload.target_address is not None:
        item.target_address = payload.target_address
    if payload.target_latitude is not None:
        item.target_latitude = payload.target_latitude
    if payload.target_longitude is not None:
        item.target_longitude = payload.target_longitude
    if payload.coord_system is not None:
        item.coord_system = str(payload.coord_system)
    if payload.geocoder_place_id is not None:
        item.geocoder_place_id = payload.geocoder_place_id
    if payload.geocoder_accuracy_m is not None:
        item.geocoder_accuracy_m = payload.geocoder_accuracy_m
    if payload.geocoding_status is not None:
        item.geocoding_status = payload.geocoding_status
    if payload.geocoded_at is not None:
        item.geocoded_at = payload.geocoded_at

    item.updated_at = datetime.now()
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch('/api/tasks/{task_id}/status', response_model=TaskResponse)
async def update_task_status(task_id: int, payload: TaskStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Task).filter(Task.id == task_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    _ensure_access(item, current_user)

    item.status = payload.status
    # 若状态更新为完成且未提供完成时间，则自动补充当前时间
    if payload.completed_at is not None:
        item.completed_at = payload.completed_at
    elif str(payload.status) == 'completed':
        item.completed_at = datetime.now()
    item.updated_at = datetime.now()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item