from pydantic import Field, validator
from .car_base import CarBase


class CarCreate(CarBase):
    """创建小车请求模型"""
    car_number: str = Field(..., max_length=50, description="小车编号")
    
    @validator('car_number')
    @classmethod
    def validate_car_number(cls, v: str) -> str:
        """验证小车编号格式"""
        if not v or len(v.strip()) == 0:
            raise ValueError('小车编号不能为空')
        
        # 小车编号格式：CAR-XXXX
        import re
        if not re.match(r'^CAR-\d{4}$', v.strip().upper()):
            raise ValueError('小车编号格式不正确，应为CAR-XXXX格式（如CAR-0001）')
            
        return v.strip().upper()