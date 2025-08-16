from pydantic import BaseModel, Field, validator
from typing import List
from .express_create import ExpressCreate


class ExpressStationInput(BaseModel):
    """驿站批量录入快递模型"""
    station_name: str = Field(..., max_length=200, description="驿站名称")
    station_address: str = Field(..., max_length=500, description="驿站地址")
    express_list: List[ExpressCreate] = Field(..., min_items=1, max_items=100, description="快递列表")
    
    @validator('station_name')
    @classmethod
    def validate_station_name(cls, v: str) -> str:
        """验证驿站名称"""
        if not v or len(v.strip()) == 0:
            raise ValueError('驿站名称不能为空')
        return v.strip()
    
    @validator('station_address')
    @classmethod
    def validate_station_address(cls, v: str) -> str:
        """验证驿站地址"""
        if not v or len(v.strip()) == 0:
            raise ValueError('驿站地址不能为空')
        if len(v.strip()) < 10:
            raise ValueError('驿站地址过于简短，请提供详细地址')
        return v.strip()
    
    @validator('express_list')
    @classmethod
    def validate_express_list(cls, v: List[ExpressCreate]) -> List[ExpressCreate]:
        """验证快递列表，确保单号不重复"""
        tracking_numbers = [express.tracking_number for express in v]
        if len(tracking_numbers) != len(set(tracking_numbers)):
            raise ValueError('快递单号不能重复')
        return v