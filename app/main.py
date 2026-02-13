"""
FastAPI主应用文件
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config.logging_config import log
from app.config.settings import settings
from app.tasks.scheduled_tasks import scheduled_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    log.info("Starting application...")
    scheduled_tasks.start()
    yield
    # 关闭时执行
    log.info("Shutting down application...")
    scheduled_tasks.stop()


# 创建FastAPI应用
app = FastAPI(
    title="Neo4j LangChain Backend",
    description="基于Neo4j和LangChain的智能笔记系统后端",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "neo4j-langchain-backend",
        "version": "1.0.0"
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Neo4j LangChain Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# 导入路由
from app.api.routes import user, category, note, event, audio, search, timeline, event_center

# 注册路由
app.include_router(user.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(category.router, prefix="/api/v1/categories", tags=["分类"])
app.include_router(note.router, prefix="/api/v1/notes", tags=["速记"])
app.include_router(event.router, prefix="/api/v1/events", tags=["事件"])
app.include_router(audio.router, prefix="/api/v1/audio", tags=["录音"])
app.include_router(search.router, prefix="/api/v1/search", tags=["搜索"])
app.include_router(timeline.router, prefix="/api/v1/timeline", tags=["时间轴"])
app.include_router(event_center.router, prefix="/api/v1/event-center", tags=["事件中心"])
