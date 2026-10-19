"""应用入口：路由注册、跨域、统一错误格式、启动初始化。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.database import Base, engine, SessionLocal
from app.models import BillCategory
from app.routers import (
    ai, auth, bills, budgets, categories, challenges, goals, notes, statistics,
)
from app.services.ai_service import AIServiceError

DEFAULT_CATEGORIES = [
    ("餐饮", "expense"), ("交通", "expense"), ("购物", "expense"), ("住房", "expense"),
    ("学习", "expense"), ("娱乐", "expense"), ("医疗", "expense"), ("通讯", "expense"),
    ("其他", "expense"),
    ("工资", "income"), ("兼职", "income"), ("理财", "income"),
    ("红包", "income"), ("退款", "income"), ("其他收入", "income"),
]


def seed_default_categories() -> None:
    """幂等写入系统预置分类（user_id 为 NULL 表示所有用户可见）。"""
    db = SessionLocal()
    try:
        for name, type_ in DEFAULT_CATEGORIES:
            exists = db.query(BillCategory).filter_by(
                user_id=None, name=name, type=type_).first()
            if exists is None:
                db.add(BillCategory(user_id=None, name=name, type=type_))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发环境便捷建表；正式部署请使用 database/schema.sql 初始化 MySQL
    Base.metadata.create_all(bind=engine)
    seed_default_categories()
    yield


app = FastAPI(
    title="智能记账与生活便签一体化管理系统 API",
    version="1.0.0",
    description="基于 FastAPI 的课程设计后端：账单、便签、预算、统计与 AI 辅助功能。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(categories.router, prefix="/api/categories", tags=["分类"])
app.include_router(bills.router, prefix="/api/bills", tags=["账单"])
app.include_router(notes.router, prefix="/api/notes", tags=["便签"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["预算"])
app.include_router(goals.router, prefix="/api/goals", tags=["储蓄目标"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["生活挑战"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["统计"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])


# 统一错误响应：{"code": HTTP状态码, "message": 提示信息}
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"code": exc.status_code, "message": str(exc.detail)})


@app.exception_handler(AIServiceError)
async def ai_exception_handler(request: Request, exc: AIServiceError):
    # AI 层异常（未配置/超时/限流/格式错误）统一转为用户可读提示
    return JSONResponse(status_code=exc.status,
                        content={"code": exc.status, "message": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    msg = first.get("msg", "参数错误")
    field = f"字段 {loc}：" if loc else ""
    return JSONResponse(status_code=422,
                        content={"code": 422, "message": f"{field}参数校验失败（{msg}）"})


@app.get("/api/health", tags=["系统"])
def health():
    return {"ok": True, "service": "smart-life-api", "version": "1.0.0"}
