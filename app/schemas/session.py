from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class SessionBase(BaseModel):
    """会话基础schema"""
    user_id: int = Field(..., description="用户ID")
    device_id: str = Field(..., max_length=255, description="设备ID")
    start_time: datetime = Field(..., description="会话开始时间")
    last_active_time: datetime = Field(..., description="最后活跃时间")
    is_active: bool = Field(default=True, description="是否活跃")
    expires_at: datetime = Field(..., description="会话过期时间")

class SessionInitializeRequest(BaseModel):
    """会话初始化请求schema"""
    userId: int = Field(..., description="用户ID")
    deviceId: str = Field(..., max_length=255, description="设备ID")
    timestamp: int = Field(..., description="时间戳")

class SessionResponse(BaseModel):
    """会话响应schema"""
    session_id: str = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    device_id: str = Field(..., description="设备ID")
    start_time: int = Field(..., description="开始时间戳")
    last_active_time: int = Field(..., description="最后活跃时间戳")
    is_active: bool = Field(..., description="是否活跃")
    
    model_config = ConfigDict(from_attributes=True)

class SessionTerminateRequest(BaseModel):
    """会话终止请求schema"""
    timestamp: int = Field(..., description="时间戳")

class SessionTerminationResponse(BaseModel):
    """会话终止响应schema"""
    success: bool = Field(..., description="是否成功")
    terminated_sessions: int = Field(..., description="终止的会话数量")
    message: Optional[str] = Field(None, description="消息")

class ForceTerminateRequest(BaseModel):
    """强制终止会话请求schema"""
    userId: int = Field(..., description="用户ID")
    excludeDeviceId: str = Field(..., description="排除的设备ID")
    timestamp: int = Field(..., description="时间戳")

class HeartbeatRequest(BaseModel):
    """心跳请求schema"""
    timestamp: int = Field(..., description="时间戳")

class HeartbeatResponse(BaseModel):
    """心跳响应schema"""
    success: bool = Field(..., description="是否成功")
    session_valid: bool = Field(..., description="会话是否有效")
    server_time: int = Field(..., description="服务器时间戳")
    message: Optional[str] = Field(None, description="消息")

class SessionValidationResponse(BaseModel):
    """会话验证响应schema"""
    valid: bool = Field(..., description="会话是否有效")

class ActivityUpdateRequest(BaseModel):
    """活跃时间更新请求schema"""
    lastActiveTime: int = Field(..., description="最后活跃时间戳")

class ActivityUpdateResponse(BaseModel):
    """活跃时间更新响应schema"""
    success: bool = Field(..., description="是否成功")

class SessionConfigResponse(BaseModel):
    """会话配置响应schema"""
    session_timeout: int = Field(..., description="会话超时时间(毫秒)")
    heartbeat_interval: int = Field(..., description="心跳间隔(毫秒)")
    max_concurrent_sessions: int = Field(..., description="最大并发会话数")

class SessionCreate(BaseModel):
    """创建会话schema"""
    user_id: int = Field(..., description="用户ID")
    device_id: str = Field(..., max_length=255, description="设备ID")

class SessionUpdate(BaseModel):
    """更新会话schema"""
    last_active_time: Optional[datetime] = Field(None, description="最后活跃时间")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class SessionFullResponse(SessionBase):
    """完整会话响应schema"""
    session_id: str = Field(..., description="会话ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)