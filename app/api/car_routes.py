from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

import time

from app.api._helpers import raise_http
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.car_service import CarService
from app.services.errors import ServiceError
from app.schemas.car import (
    CarCreate,
    CarUpdate,
    CarResponse,
    CarLocationUpdate,
    CarStatusUpdate,
)
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

router = APIRouter()
_car_service = CarService()


@router.post('/api/cars', response_model=CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(payload: CarCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建小车（协议保持不变）。"""
    try:
        return _car_service.create_car(db=db, current_user=current_user, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/cars/{car_id}', response_model=CarResponse)
async def get_car(car_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取小车详情（协议保持不变）。"""
    try:
        return _car_service.get_car(db=db, current_user=current_user, car_id=car_id)
    except ServiceError as e:
        raise_http(e)


@router.get('/api/cars', response_model=List[CarResponse])
async def list_cars(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出小车列表（协议保持不变）。"""
    try:
        return _car_service.list_cars(db=db, current_user=current_user)
    except ServiceError as e:
        raise_http(e)


@router.put('/api/cars/{car_id}', response_model=CarResponse)
async def update_car(car_id: int, payload: CarUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新小车（协议保持不变）。"""
    try:
        return _car_service.update_car(db=db, current_user=current_user, car_id=car_id, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.patch('/api/cars/{car_id}/location', response_model=CarResponse)
async def update_car_location(car_id: int, payload: CarLocationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新小车位置（协议保持不变）。"""
    try:
        return _car_service.update_car_location(db=db, current_user=current_user, car_id=car_id, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.patch('/api/cars/{car_id}/status', response_model=CarResponse)
async def update_car_status(car_id: int, payload: CarStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新小车状态（协议保持不变）。"""
    try:
        return _car_service.update_car_status(db=db, current_user=current_user, car_id=car_id, payload=payload)
    except ServiceError as e:
        raise_http(e)


@router.websocket('/ws/cars/{car_id}/video')
async def car_video_stream(websocket: WebSocket, car_id: int):
    # 接受来自小车的视频流（二进制帧）
    await websocket.accept()
    frame_count = 0
    try:
        while True:
            message = await websocket.receive()
            frame = message.get('bytes')
            if frame is not None:
                # 这里只接收帧，不做存储或转码，保持最小实现
                frame_count += 1
                # 轻量反馈（可选），避免过度回传影响带宽
                if frame_count % 30 == 0:
                    await websocket.send_text(f"received {frame_count} frames for {car_id}")
            else:
                text = message.get('text')
                if text == 'ping':
                    await websocket.send_text('pong')
                else:
                    # 对于非视频文本消息做最小响应
                    await websocket.send_text('ok')
    except WebSocketDisconnect:
        # 客户端主动断开
        pass
    except Exception:
        # 非预期错误，关闭连接
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.websocket('/ws/cars/{car_id}/control')
async def car_control_channel(websocket: WebSocket, car_id: int):
    # 接入后立即发送占位JSON，供未来扩展为控制指令
    await websocket.accept()
    placeholder = {
        "type": "control_placeholder",
        "car_id": car_id,
        "ts": int(time.time() * 1000),
    }
    try:
        await websocket.send_json(placeholder)
        # 保持连接以便未来扩展（当前不做额外交互）
        while True:
            message = await websocket.receive()
            text = message.get("text")
            if text == "ping":
                await websocket.send_text("pong")
            elif text == "close":
                await websocket.close()
                break
            else:
                # 其他消息忽略，保持连接
                pass
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass