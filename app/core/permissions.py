from enum import Enum
from app.models.enums import UserRole
from app.services.errors import ServiceError


class Permission(str, Enum):
    PROFILE = "profile:edit"
    USER_READ = "user:read"
    USER_ALL = "user:read_all"
    APPOINTMENT = "appointment:access"
    APPOINTMENT_ALL = "appointment:manage_all"
    EXPRESS = "express:read"
    EXPRESS_CREATE = "express:create"
    EXPRESS_ALL = "express:manage_all"
    TASK = "task:read"
    TASK_ALL = "task:manage_all"
    CAR = "car:manage"
    DISPATCH = "task:dispatch"
    ADDRESS = "address:access"
    ADDRESS_ALL = "address:manage_all"
    ANNOUNCEMENT = "announcement:manage"
    MAP = "map:query"


ROLE_PERMISSIONS = {
    UserRole.admin: frozenset(Permission),
    UserRole.customer: frozenset({Permission.PROFILE, Permission.USER_READ,
        Permission.APPOINTMENT, Permission.EXPRESS, Permission.EXPRESS_CREATE,
        Permission.TASK, Permission.ADDRESS, Permission.MAP}),
    UserRole.others: frozenset(),
}


def has_permission(user, permission: Permission) -> bool:
    return bool(user and user.is_active and
                permission in ROLE_PERMISSIONS.get(user.role, frozenset()))


def require_permission(user, permission: Permission) -> None:
    if not has_permission(user, permission):
        raise ServiceError(status_code=403, detail="无权限执行该操作")


def require_owner(user, permission: Permission, all_permission: Permission, owner_id) -> None:
    require_permission(user, permission)
    if owner_id != user.id and not has_permission(user, all_permission):
        raise ServiceError(status_code=403, detail="无权限访问该资源")
