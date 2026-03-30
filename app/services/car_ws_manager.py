from __future__ import annotations

import asyncio
from typing import Dict, Optional

from fastapi import WebSocket

_control_connections: Dict[int, WebSocket] = {}
_lock = asyncio.Lock()


async def register_car_control_connection(car_id: int, websocket: WebSocket) -> None:
    """注册小车 control WebSocket 连接（按车 ID 覆盖旧连接）。"""
    async with _lock:
        _control_connections[car_id] = websocket


async def unregister_car_control_connection(car_id: int) -> None:
    """注销小车 control WebSocket 连接。"""
    async with _lock:
        _control_connections.pop(car_id, None)


async def get_car_control_connection(car_id: int) -> Optional[WebSocket]:
    async with _lock:
        return _control_connections.get(car_id)


async def send_car_control_message(car_id: int, payload: dict) -> bool:
    """向指定小车下发 control 指令；连接不存在返回 False。"""
    websocket = await get_car_control_connection(car_id)
    if not websocket:
        return False

    try:
        await websocket.send_json(payload)
        return True
    except Exception:
        # 连接可能已断开或处于异常状态
        await unregister_car_control_connection(car_id)
        return False

