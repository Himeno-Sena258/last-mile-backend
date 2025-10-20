from fastapi import APIRouter
from app.api.routes import app as user_router
from app.api.session_routes import router as session_router
from app.api.appointment_routes import router as appointment_router

router = APIRouter()

# 注册用户相关路由
router.include_router(user_router)

# 注册会话相关路由
router.include_router(session_router)

# 注册预约相关路由
router.include_router(appointment_router)