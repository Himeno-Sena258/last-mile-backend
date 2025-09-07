from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class BaseSchema(BaseModel):
    """所有模型的基础模型类"""
    id: Optional[int] = Field(None, description="记录ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    # Pydantic v2 配置
    model_config = ConfigDict(from_attributes=True)