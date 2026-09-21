from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import WebSocket
from app.core.device_security import require_device
from app.db.database import SessionLocal
from app.services.errors import ServiceError

_control_connections: Dict[int, WebSocket] = {}
_last_seen: Dict[int, datetime] = {}
_last_ping: Dict[int, datetime] = {}
_lock = asyncio.Lock()

HEARTBEAT_INTERVAL_SECONDS = 5
HEARTBEAT_TIMEOUT_SECONDS = 15


async def register_car_control_connection(car_id: int, websocket: WebSocket) -> None:
    """注册小车 control WebSocket 连接（按车 ID 覆盖旧连接）。"""
    async with _lock:
        _control_connections[car_id] = websocket
        now = datetime.now()
        _last_seen[car_id] = now
        _last_ping[car_id] = now


async def unregister_car_control_connection(car_id: int, websocket: Optional[WebSocket] = None) -> bool:
    """注销小车 control WebSocket 连接。"""
    async with _lock:
        if websocket is None or _control_connections.get(car_id) is websocket:
            _control_connections.pop(car_id, None)
            _last_seen.pop(car_id, None)
            _last_ping.pop(car_id, None)
            return True
        return False


async def touch_car_connection(car_id: int, websocket: WebSocket) -> bool:
    async with _lock:
        if _control_connections.get(car_id) is not websocket:
            return False
        _last_seen[car_id] = datetime.now()
        return True


async def get_car_control_connection(car_id: int) -> Optional[WebSocket]:
    async with _lock:
        websocket = _control_connections.get(car_id)
        seen = _last_seen.get(car_id)
        if not websocket or not seen or datetime.now() - seen > timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS):
            return None
        return websocket


async def heartbeat_connections(db) -> list[int]:
    """Ping live sockets and remove connections that stopped replying."""
    now = datetime.now()
    async with _lock:
        snapshot = [(car_id, socket, _last_seen.get(car_id), _last_ping.get(car_id))
                    for car_id, socket in _control_connections.items()]
    offline = []
    for car_id, websocket, seen, last_ping in snapshot:
        if not seen or now - seen > timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS):
            if await unregister_car_control_connection(car_id, websocket):
                offline.append(car_id)
            try:
                await websocket.close(code=1011)
            except Exception:
                pass
            continue
        if not last_ping or now - last_ping >= timedelta(seconds=HEARTBEAT_INTERVAL_SECONDS):
            try:
                require_device(db, car_id, websocket.headers.get("authorization", ""))
                await websocket.send_json({"type": "heartbeat", "ts": int(now.timestamp() * 1000)})
                async with _lock:
                    if _control_connections.get(car_id) is websocket:
                        _last_ping[car_id] = now
            except Exception:
                if await unregister_car_control_connection(car_id, websocket):
                    offline.append(car_id)
                try:
                    await websocket.close(code=1008)
                except Exception:
                    pass
    return offline


async def send_car_control_message(car_id: int, payload: dict) -> bool:
    """向指定小车下发 control 指令；连接不存在返回 False。"""
    websocket = await get_car_control_connection(car_id)
    if not websocket:
        return False

    try:
        with SessionLocal() as db:
            require_device(db, car_id, websocket.headers.get("authorization", ""))
        await websocket.send_json(payload)
        return True
    except ServiceError:
        await unregister_car_control_connection(car_id, websocket)
        await websocket.close(code=1008)
        return False
    except Exception:
        # 连接可能已断开或处于异常状态
        await unregister_car_control_connection(car_id, websocket)
        return False

