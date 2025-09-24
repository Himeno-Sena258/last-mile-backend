from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.services.session_service import SessionService
from app.schemas.session import (
    SessionInitializeRequest, SessionResponse, SessionTerminateRequest,
    SessionTerminationResponse, ForceTerminateRequest, HeartbeatRequest,
    HeartbeatResponse, SessionValidationResponse, ActivityUpdateRequest,
    ActivityUpdateResponse, SessionConfigResponse
)
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/user-sessions", tags=["user-sessions"])

def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """
    获取会话服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        SessionService: 会话服务实例
    """
    return SessionService(db)

@router.post("/initialize", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def initialize_user_session(
    request: SessionInitializeRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    初始化用户会话（强制其他设备下线）
    
    Args:
        request: 会话初始化请求
        session_service: 会话服务
        
    Returns:
        SessionResponse: 会话信息
    """
    try:
        return session_service.initialize_user_session(
            user_id=request.userId,
            device_id=request.deviceId
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化会话失败"
        )

@router.post("/{session_id}/terminate", response_model=SessionTerminationResponse)
async def terminate_user_session(
    session_id: str,
    request: SessionTerminateRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    终止指定会话
    
    Args:
        session_id: 会话ID
        request: 会话终止请求
        session_service: 会话服务
        
    Returns:
        SessionTerminationResponse: 终止结果
    """
    try:
        return session_service.terminate_user_session(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="终止会话失败"
        )

@router.post("/force-terminate", response_model=SessionTerminationResponse)
async def force_terminate_user_sessions(
    request: ForceTerminateRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    强制终止用户的所有其他会话
    
    Args:
        request: 强制终止请求
        session_service: 会话服务
        
    Returns:
        SessionTerminationResponse: 终止结果
    """
    try:
        return session_service.force_terminate_user_sessions(
            user_id=request.userId,
            exclude_device_id=request.excludeDeviceId
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="强制终止会话失败"
        )

@router.post("/{session_id}/heartbeat", response_model=HeartbeatResponse)
async def send_user_heartbeat(
    session_id: str,
    request: HeartbeatRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    发送用户心跳信号
    
    Args:
        session_id: 会话ID
        request: 心跳请求
        session_service: 会话服务
        
    Returns:
        HeartbeatResponse: 心跳响应
    """
    try:
        return session_service.send_user_heartbeat(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="心跳检测失败"
        )

@router.get("/active/{user_id}", response_model=List[SessionResponse])
async def get_user_active_sessions(
    user_id: int,
    session_service: SessionService = Depends(get_session_service)
):
    """
    获取用户当前活跃会话信息
    
    Args:
        user_id: 用户ID
        session_service: 会话服务
        
    Returns:
        List[SessionResponse]: 会话信息列表
    """
    try:
        return session_service.get_user_active_sessions(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取活跃会话失败"
        )

@router.get("/{session_id}/validate", response_model=SessionValidationResponse)
async def validate_user_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """
    验证会话是否有效
    
    Args:
        session_id: 会话ID
        session_service: 会话服务
        
    Returns:
        SessionValidationResponse: 验证结果
    """
    try:
        return session_service.validate_user_session(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证会话失败"
        )

@router.put("/{session_id}/activity", response_model=ActivityUpdateResponse)
async def update_session_activity(
    session_id: str,
    request: ActivityUpdateRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    更新会话的最后活跃时间
    
    Args:
        session_id: 会话ID
        request: 活跃时间更新请求
        session_service: 会话服务
        
    Returns:
        ActivityUpdateResponse: 更新结果
    """
    try:
        return session_service.update_session_activity(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新会话活跃时间失败"
        )

@router.get("/config", response_model=SessionConfigResponse)
async def get_session_config(
    session_service: SessionService = Depends(get_session_service)
):
    """
    获取会话超时配置
    
    Args:
        session_service: 会话服务
        
    Returns:
        SessionConfigResponse: 超时配置信息
    """
    try:
        return session_service.get_session_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话配置失败"
        )