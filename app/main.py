"""
智能图像鉴伪辅助平台 - 主应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import tasks, analysis, cases

# 导入所有模型以确保它们被注册
from app.models import AuditTask, ImageFile, AnalysisResult, CaseLibraryEntry

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用实例
app = FastAPI(
    title="智能图像鉴伪辅助平台",
    description="基于AI的图像伪造检测系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 注册API路由
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(cases.router, prefix="/api/v1", tags=["cases"])

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 智能图像鉴伪辅助平台启动成功")
    logger.info(f"📊 API文档地址: http://localhost:8000/docs")
    
    # 确保上传目录存在
    os.makedirs("app/static/uploads", exist_ok=True)
    os.makedirs("app/static/processed", exist_ok=True)

    # 兼容历史数据：将旧的大写状态值规范化为小写（与枚举一致）
    try:
        with engine.begin() as conn:
            # 分别执行每个UPDATE语句
            conn.exec_driver_sql("UPDATE audit_tasks SET status='processing' WHERE status='PROCESSING'")
            conn.exec_driver_sql("UPDATE audit_tasks SET status='pending_review' WHERE status='PENDING_REVIEW'")
            conn.exec_driver_sql("UPDATE audit_tasks SET status='confirmed_forgery' WHERE status='CONFIRMED_FORGERY'")
            conn.exec_driver_sql("UPDATE audit_tasks SET status='confirmed_safe' WHERE status='CONFIRMED_SAFE'")
            logger.info("状态规范化迁移完成")
    except Exception as e:
        logger.warning(f"状态规范化迁移失败: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 智能图像鉴伪辅助平台已关闭")

@app.get("/")
async def root():
    """根路径 - 系统状态检查"""
    return {
        "message": "智能图像鉴伪辅助平台",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "image-forgery-detection"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )