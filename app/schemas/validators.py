from typing import Optional, Any, Type, TypeVar, Callable, Dict, Union
from pydantic import field_validator, Field, ValidationInfo
import re
from datetime import datetime, timedelta

# 类型变量，用于泛型函数返回类型
T = TypeVar('T')

# 通用错误消息
ERROR_MESSAGES = {
    "required": "该字段不能为空",
    "min_length": "长度不能少于{min_length}个字符",
    "max_length": "长度不能超过{max_length}个字符",
    "range": "{field_name}必须在{min_value}到{max_value}之间",
    "pattern": "{field_name}格式不正确",
    "future_time": "{field_name}不能是过去时间",
    "max_future_time": "{field_name}不能超过{days}天",
}

# 通用正则表达式模式
PATTERNS = {
    "phone": r'^1[3-9]\d{9}$',  # 中国手机号
    "car_number": r'^CAR-\d{4}$',  # 小车编号格式
    "tracking_number": r'^[A-Za-z0-9\-]+$',  # 快递单号格式
}


def validate_non_empty_string(v: Optional[str], *, field_name: str = "字段") -> str:
    """验证非空字符串
    
    Args:
        v: 要验证的字符串
        field_name: 字段名称，用于错误消息
        
    Returns:
        清理后的字符串
        
    Raises:
        ValueError: 如果字符串为空
    """
    if v is None or len(v.strip()) == 0:
        raise ValueError(f"{field_name}{ERROR_MESSAGES['required']}")
    return v.strip()


def validate_string_length(v: Optional[str], *, min_length: int = None, 
                        max_length: int = None, field_name: str = "字段") -> Optional[str]:
    """验证字符串长度
    
    Args:
        v: 要验证的字符串
        min_length: 最小长度
        max_length: 最大长度
        field_name: 字段名称，用于错误消息
        
    Returns:
        清理后的字符串或None
        
    Raises:
        ValueError: 如果字符串长度不符合要求
    """
    if v is None:
        return None
        
    v = v.strip()
    if not v:
        return None
        
    if min_length is not None and len(v) < min_length:
        raise ValueError(ERROR_MESSAGES["min_length"].format(min_length=min_length))
        
    if max_length is not None and len(v) > max_length:
        raise ValueError(ERROR_MESSAGES["max_length"].format(max_length=max_length))
        
    return v


def validate_pattern(v: Optional[str], *, pattern: str, 
                    pattern_name: Optional[str] = None, 
                    field_name: str = "字段") -> Optional[str]:
    """验证字符串模式
    
    Args:
        v: 要验证的字符串
        pattern: 正则表达式模式或预定义模式名称
        pattern_name: 模式名称，用于错误消息
        field_name: 字段名称，用于错误消息
        
    Returns:
        清理后的字符串或None
        
    Raises:
        ValueError: 如果字符串不符合模式
    """
    if v is None:
        return None
        
    v = v.strip()
    if not v:
        return None
        
    # 如果pattern是预定义模式的名称，则获取对应的正则表达式
    if pattern in PATTERNS:
        regex_pattern = PATTERNS[pattern]
    else:
        regex_pattern = pattern
        
    if not re.match(regex_pattern, v):
        pattern_desc = pattern_name or pattern
        raise ValueError(ERROR_MESSAGES["pattern"].format(field_name=field_name))
        
    # 对特定模式进行格式化处理
    if pattern == "car_number" or pattern == PATTERNS["car_number"]:
        return v.upper()
    elif pattern == "tracking_number" or pattern == PATTERNS["tracking_number"]:
        return v.upper()
    
    return v


def validate_numeric_range(v: Optional[Union[int, float]], *, 
                          min_value: Optional[Union[int, float]] = None, 
                          max_value: Optional[Union[int, float]] = None,
                          field_name: str = "数值",
                          round_digits: Optional[int] = None) -> Optional[Union[int, float]]:
    """验证数值范围
    
    Args:
        v: 要验证的数值
        min_value: 最小值
        max_value: 最大值
        field_name: 字段名称，用于错误消息
        round_digits: 四舍五入的小数位数
        
    Returns:
        验证后的数值或None
        
    Raises:
        ValueError: 如果数值不在指定范围内
    """
    if v is None:
        return None
        
    if min_value is not None and v < min_value:
        raise ValueError(ERROR_MESSAGES["range"].format(
            field_name=field_name, min_value=min_value, max_value=max_value or "无限"))
        
    if max_value is not None and v > max_value:
        raise ValueError(ERROR_MESSAGES["range"].format(
            field_name=field_name, min_value=min_value or "无限", max_value=max_value))
        
    if round_digits is not None and isinstance(v, float):
        return round(v, round_digits)
        
    return v


def validate_future_datetime(v: Optional[datetime], *, 
                            max_days: Optional[int] = None,
                            field_name: str = "时间") -> Optional[datetime]:
    """验证未来时间
    
    Args:
        v: 要验证的时间
        max_days: 最大天数
        field_name: 字段名称，用于错误消息
        
    Returns:
        验证后的时间或None
        
    Raises:
        ValueError: 如果时间不是未来时间或超过最大天数
    """
    if v is None:
        return None
        
    now = datetime.now()
    
    # 验证是否为未来时间
    if v <= now:
        raise ValueError(ERROR_MESSAGES["future_time"].format(field_name=field_name))
        
    # 验证是否超过最大天数
    if max_days is not None:
        max_future_time = now + timedelta(days=max_days)
        if v > max_future_time:
            raise ValueError(ERROR_MESSAGES["max_future_time"].format(
                field_name=field_name, days=max_days))
                
    return v


# 创建字段验证器装饰器工厂函数
def create_validator(validator_func: Callable, **kwargs) -> Callable:
    """创建字段验证器装饰器
    
    Args:
        validator_func: 验证函数
        **kwargs: 传递给验证函数的关键字参数
        
    Returns:
        字段验证器装饰器函数
    """
    @field_validator
    @classmethod
    def validator(cls, v: Any, info: ValidationInfo) -> Any:
        field_name = info.field_name
        return validator_func(v, field_name=field_name, **kwargs)
        
    return validator