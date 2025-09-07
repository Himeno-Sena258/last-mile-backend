"""存储schemas中使用的常量值"""

# 字符串长度限制
MAX_LENGTHS = {
    "username": 50,
    "name": 100,
    "phone": 20,
    "address": 500,
    "tracking_number": 100,
    "station_name": 200,
    "station_address": 500,
    "notes": 500,
    "description": 1000,
    "route_name": 200,
}

MIN_LENGTHS = {
    "username": 3,
}

# 数值范围限制
NUMERIC_RANGES = {
    "total_distance": {"min": 0.0, "max": 1000.0},  # km
    "estimated_duration": {"min": 0, "max": 1440},  # 分钟，最大24小时
    "current_speed": {"min": 0.0, "max": 50.0},  # km/h
    "latitude": {"min": -90.0, "max": 90.0},
    "longitude": {"min": -180.0, "max": 180.0},
    "battery_level": {"min": 0.0, "max": 100.0},  # 百分比
}

# 时间限制
TIME_LIMITS = {
    "max_future_days": 7,  # 最大未来天数
}

# 字段描述
FIELD_DESCRIPTIONS = {
    "id": "记录ID",
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "username": "用户名",
    "email": "电子邮箱",
    "name": "姓名",
    "phone": "电话号码",
    "address": "地址",
    "role": "用户角色",
    "tracking_number": "快递单号",
    "recipient_name": "收件人姓名",
    "recipient_phone": "收件人电话",
    "recipient_address": "收件人地址",
    "recipient_user_id": "收件人用户ID",
    "status": "状态",
    "station_name": "驿站名称",
    "station_address": "驿站地址",
    "customer_id": "客户ID",
    "express_tracking_number": "快递单号",
    "appointment_time": "预约时间",
    "notes": "备注",
    "task_status": "任务状态",
    "current_task_id": "当前任务ID",
    "current_speed": "当前速度(km/h)",
    "current_latitude": "当前纬度",
    "current_longitude": "当前经度",
    "battery_level": "电量百分比",
    "running_time": "已运行时间(分钟)",
    "is_active": "是否激活",
    "assigned_car_number": "分配的小车编号",
    "expected_completion_time": "任务预计完成时间",
    "route_id": "路线ID",
    "name": "名称",
    "description": "描述",
    "total_distance": "总距离(km)",
    "estimated_duration": "预计耗时(分钟)",
}