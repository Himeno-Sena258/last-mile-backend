from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api import router as api_router
from app.db.database import engine
import app.models as models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 仅针对 /api/regeo 打印校验失败细节，便于前后端联调定位字段问题
    if request.url.path == "/api/regeo":
        errors = exc.errors()
        # 只打印必要的字段信息，避免刷屏和打印到 <unreadable body>
        simple = "; ".join(
            f"{'.'.join(map(str, e.get('loc', [])))}: {e.get('msg', '')}" for e in errors
        )
        print(f"[regeo-422] {simple}")

    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
