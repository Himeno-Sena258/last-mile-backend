from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
import time
from app.models.session import UserSession
from app.models.user import User
from app.schemas.session import (
    SessionResponse, SessionTerminationResponse, HeartbeatResponse,
    SessionValidationResponse, ActivityUpdateResponse, SessionConfigResponse
)

class SessionService:
    """用户会话服务类"""
    
    # 会话配置常量
    SESSION_TIMEOUT_MINUTES = 30  # 会话超时时间（分钟）
    HEARTBEAT_INTERVAL_MINUTES = 5  # 心跳间隔（分钟）
    MAX_CONCURRENT_SESSIONS = 1  # 最大并发会话数
    
    def __init__(self, db: Session):
        """
        初始化会话服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def generate_session_id(self) -> str:
        """
        生成唯一的会话ID
        
        Returns:
            str: 会话ID
        """
        return str(uuid.uuid4())
    
    def initialize_user_session(self, user_id: int, device_id: str) -> SessionResponse:
        """
        初始化用户会话（强制其他设备下线）
        
        Args:
            user_id: 用户ID
            device_id: 设备ID
            
        Returns:
            SessionResponse: 会话信息
        """
        # 检查用户是否存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"用户 {user_id} 不存在")
        
        # 强制终止该用户的所有其他会话
        self.force_terminate_user_sessions(user_id, device_id)
        
        # 创建新会话
        now = datetime.now()
        expires_at = now + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        session_id = self.generate_session_id()
        
        new_session = UserSession(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            start_time=now,
            last_active_time=now,
            is_active=True,
            expires_at=expires_at
        )
        
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return SessionResponse(
            session_id=new_session.session_id,
            user_id=new_session.user_id,
            device_id=new_session.device_id,
            start_time=int(new_session.start_time.timestamp() * 1000),
            last_active_time=int(new_session.last_active_time.timestamp() * 1000),
            is_active=new_session.is_active
        )
    
    def terminate_user_session(self, session_id: str) -> SessionTerminationResponse:
        """
        终止指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            SessionTerminationResponse: 终止结果
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session:
            return SessionTerminationResponse(
                success=False,
                terminated_sessions=0,
                message="会话不存在"
            )
        
        # 标记会话为非活跃
        session.is_active = False
        self.db.commit()
        
        return SessionTerminationResponse(
            success=True,
            terminated_sessions=1,
            message="会话已成功终止"
        )
    
    def force_terminate_user_sessions(self, user_id: int, exclude_device_id: str) -> SessionTerminationResponse:
        """
        强制终止用户的所有其他会话
        
        Args:
            user_id: 用户ID
            exclude_device_id: 排除的设备ID
            
        Returns:
            SessionTerminationResponse: 终止结果
        """
        # 查找该用户除了指定设备外的所有活跃会话
        sessions_to_terminate = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.device_id != exclude_device_id,
                UserSession.is_active == True
            )
        ).all()
        
        terminated_count = len(sessions_to_terminate)
        
        # 终止这些会话
        for session in sessions_to_terminate:
            session.is_active = False
        
        self.db.commit()
        
        return SessionTerminationResponse(
            success=True,
            terminated_sessions=terminated_count,
            message=f"已终止 {terminated_count} 个会话"
        )
    
    def send_user_heartbeat(self, session_id: str) -> HeartbeatResponse:
        """
        处理用户心跳信号
        
        Args:
            session_id: 会话ID
            
        Returns:
            HeartbeatResponse: 心跳响应
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session:
            return HeartbeatResponse(
                success=False,
                session_valid=False,
                server_time=int(time.time() * 1000),
                message="会话不存在"
            )
        
        # 检查会话是否过期
        now = datetime.now()
        if now > session.expires_at or not session.is_active:
            session.is_active = False
            self.db.commit()
            return HeartbeatResponse(
                success=False,
                session_valid=False,
                server_time=int(time.time() * 1000),
                message="会话已过期"
            )
        
        # 更新最后活跃时间和过期时间
        session.last_active_time = now
        session.expires_at = now + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        self.db.commit()
        
        return HeartbeatResponse(
            success=True,
            session_valid=True,
            server_time=int(time.time() * 1000),
            message="心跳成功"
        )
    
    def get_user_active_sessions(self, user_id: int) -> List[SessionResponse]:
        """
        获取用户当前活跃会话信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[SessionResponse]: 会话信息列表
        """
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).all()
        
        return [
            SessionResponse(
                session_id=session.session_id,
                user_id=session.user_id,
                device_id=session.device_id,
                start_time=int(session.start_time.timestamp() * 1000),
                last_active_time=int(session.last_active_time.timestamp() * 1000),
                is_active=session.is_active
            )
            for session in sessions
        ]
    
    def validate_user_session(self, session_id: str) -> SessionValidationResponse:
        """
        验证会话是否有效
        
        Args:
            session_id: 会话ID
            
        Returns:
            SessionValidationResponse: 验证结果
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session:
            return SessionValidationResponse(valid=False)
        
        # 检查会话是否过期或非活跃
        now = datetime.now()
        if now > session.expires_at or not session.is_active:
            # 标记会话为非活跃
            session.is_active = False
            self.db.commit()
            return SessionValidationResponse(valid=False)
        
        return SessionValidationResponse(valid=True)
    
    def update_session_activity(self, session_id: str) -> ActivityUpdateResponse:
        """
        更新会话的最后活跃时间
        
        Args:
            session_id: 会话ID
            
        Returns:
            ActivityUpdateResponse: 更新结果
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session or not session.is_active:
            return ActivityUpdateResponse(success=False)
        
        # 检查会话是否过期
        now = datetime.now()
        if now > session.expires_at:
            session.is_active = False
            self.db.commit()
            return ActivityUpdateResponse(success=False)
        
        # 更新最后活跃时间和过期时间
        session.last_active_time = now
        session.expires_at = now + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        self.db.commit()
        
        return ActivityUpdateResponse(success=True)
    
    def get_session_config(self) -> SessionConfigResponse:
        """
        获取会话超时配置
        
        Returns:
            SessionConfigResponse: 超时配置信息
        """
        return SessionConfigResponse(
            session_timeout=self.SESSION_TIMEOUT_MINUTES * 60 * 1000,  # 转换为毫秒
            heartbeat_interval=self.HEARTBEAT_INTERVAL_MINUTES * 60 * 1000,  # 转换为毫秒
            max_concurrent_sessions=self.MAX_CONCURRENT_SESSIONS
        )
    
    def _cleanup_expired_sessions(self):
        """
        清理过期的会话
        """
        now = datetime.now()
        expired_sessions = self.db.query(UserSession).filter(
            or_(
                UserSession.expires_at < now,
                UserSession.is_active == False
            )
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
        
        self.db.commit()
    
    def get_session_by_id(self, session_id: str) -> Optional[UserSession]:
        """
        根据会话ID获取会话对象
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[UserSession]: 会话对象或None
        """
        return self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()