from fastapi import APIRouter
from app.api.user_routes import app as user_router
from app.api.appointment_routes import router as appointment_router
from app.api.task_routes import router as task_router
from app.api.express_routes import router as express_router
from app.api.car_routes import router as car_router
from app.api.geocoding_routes import router as geocoding_router
from app.api.regeo_routes import router as regeo_router
from app.api.dispatch_routes import router as dispatch_router
from app.api.announcement_routes import router as announcement_router
from app.api.address_routes import router as address_router

router = APIRouter()

# 注册用户相关路由
router.include_router(user_router)

# 注册预约相关路由
router.include_router(appointment_router)

# 注册任务相关路由
router.include_router(task_router)

# 注册快递相关路由
router.include_router(express_router)

# 注册小车相关路由
router.include_router(car_router)

# 注册地理编码相关路由
router.include_router(geocoding_router)

# 注册逆地理 + POI 路由
router.include_router(regeo_router)

# 注册任务调度路由
router.include_router(dispatch_router)

# 注册公告路由
router.include_router(announcement_router)

# 注册地址路由
router.include_router(address_router)