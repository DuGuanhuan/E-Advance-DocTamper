"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "智能图像鉴伪辅助平台"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite:///./app/data/app.db"
    
    # 文件上传配置
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg", 
        "image/png", 
        "image/jpg", 
        "application/pdf"
    ]
    upload_dir: str = "app/static/uploads"
    processed_dir: str = "app/static/processed"
    
    # 相似图检索 - 图片库与向量数据库
    image_library_dir: str = "app/data/image_library"
    chroma_db_dir: str = "app/data/chroma_db"
    chroma_collection_name: str = "image_library"
    similarity_threshold: float = 0.9  # > 90%
    
    # AI服务配置
    ai_api_url: str = "http://localhost:9000/api/detect"
    ai_api_key: str = ""
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "app/logs/app.log"
    
    # 安全配置
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        settings.upload_dir,
        settings.processed_dir,
        "app/data",
        "app/logs",
        settings.image_library_dir,
        settings.chroma_db_dir
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 初始化目录
ensure_directories()
