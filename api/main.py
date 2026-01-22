"""
FastAPI 主应用
API 服务入口点
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import logging
import time
import json

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from infra.config import config
from api.pic import router as pic_router
from api.dependencies import get_client_ip, generate_request_id

# 配置日志
logging.basicConfig(
    level=logging.INFO if config.app.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时执行初始化
    关闭时执行清理
    """
    # 启动时
    logger.info("🚀 启动 AI 图片生成 API 服务")
    logger.info(f"   环境: {config.app.env}")
    logger.info(f"   调试模式: {config.app.debug}")
    logger.info(f"   主机: {config.server.host}")
    logger.info(f"   端口: {config.server.port}")
    logger.info(f"   数据库: {config.database.url.split('?')[0] if '?' in config.database.url else config.database.url}")
    
    # 创建必要的目录
    Path("./static/images").mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(exist_ok=True)
    
    # 检查 AI 配置
    from services.ai_service import get_ai_service
    ai_service = get_ai_service()
    if ai_service.api_key and "your-" not in ai_service.api_key:
        logger.info("✅ AI 服务已配置")
    else:
        logger.warning("⚠️  AI 服务未配置，将使用模拟数据")
    
    yield  # 应用运行
    
    # 关闭时
    logger.info("🛑 关闭 API 服务")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI 图片生成 API",
    description="通过 AI 模型生成图片的 Web API 服务",
    version="1.0.0",
    docs_url="/docs" if config.app.debug else None,
    redoc_url="/redoc" if config.app.debug else None,
    openapi_url="/openapi.json" if config.app.debug else None,
    lifespan=lifespan,
)


# ==================== 中间件 ====================
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    日志中间件
    记录所有 HTTP 请求
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    # 获取请求信息
    client_ip = get_client_ip(request)
    method = request.method
    url = str(request.url)
    
    # 记录请求开始
    logger.info(f"📥 请求开始 [{request_id}]: {method} {url} from {client_ip}")
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        logger.info(
            f"📤 请求完成 [{request_id}]: {method} {url} "
            f"status={response.status_code} time={process_time:.3f}s"
        )
        
        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
        
    except Exception as e:
        # 记录异常
        process_time = time.time() - start_time
        logger.error(
            f"💥 请求异常 [{request_id}]: {method} {url} "
            f"error={e} time={process_time:.3f}s"
        )
        raise


# CORS 中间件
if config.app.env == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ==================== 静态文件 ====================
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== 路由 ====================
@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "🎨 AI 图片生成 API",
        "version": "1.0.0",
        "docs": "/docs" if config.app.debug else None,
        "health": "/health",
        "endpoints": {
            "生成图片": "POST /api/generate",
            "获取任务": "GET /api/tasks/{id}",
            "任务列表": "GET /api/tasks",
            "系统状态": "GET /api/status",
        }
    }


# 包含图片相关路由
app.include_router(pic_router, prefix="/api")


# ==================== 异常处理 ====================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.warning(f"❌ 请求验证失败: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "请求数据格式错误",
            "errors": exc.errors(),
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    logger.warning(f"⚠️  HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
        headers=exc.headers or {},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"💥 未处理异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误",
            "message": str(exc) if config.app.debug else "请稍后重试"
        }
    )


# ==================== 运行应用 ====================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.app.debug,
        log_level="info" if config.app.debug else "warning",
    )
