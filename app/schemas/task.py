"""
任务相关的Pydantic模式
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.core.constants import TaskStatus


class ImageFileResponse(BaseModel):
    """图片文件响应模型"""
    file_id: str
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: TaskStatus
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    files: List[ImageFileResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskCreateResponse(BaseModel):
    """任务创建响应模型"""
    task_id: str
    status: TaskStatus
    message: str = "任务创建成功"


class HistoricalMatch(BaseModel):
    """历史匹配图片模型"""
    filename: str
    url: str
    similarity: float  # 相似度 0.0-1.0
    diff_details: str

class AIFinding(BaseModel):
    """AI检测发现模型"""
    type: str
    detail: str

class AnalysisResult(BaseModel):
    """分析结果模型"""
    historical_matches: List[HistoricalMatch] = Field(default_factory=list)
    ai_findings: List[AIFinding] = Field(default_factory=list)

class UploadedImage(BaseModel):
    """上传图片信息模型"""
    filename: str
    url: str

class TaskDetailResponse(BaseModel):
    """任务详情响应模型"""
    task_id: str
    status: TaskStatus
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    files: List[ImageFileResponse] = Field(default_factory=list)
    file_count: int = 0
    total_file_size: int = 0  # 总文件大小（字节）
    uploaded_image: Optional[UploadedImage] = None
    analysis_result: Optional[AnalysisResult] = None

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 10


class AnnotationBox(BaseModel):
    """标注框模型（支持比例坐标0-1）"""
    x: float
    y: float
    width: float
    height: float

class TaskConfirmRequest(BaseModel):
    """任务确认请求模型 - 根据PRD要求"""
    is_forgery: bool
    forgery_types: Optional[List[str]] = None
    notes: Optional[str] = None
    annotations: Optional[List[AnnotationBox]] = None  # 支持多个标注框
    bounding_box: Optional[dict] = None  # 保持向后兼容


class TaskConfirmResponse(BaseModel):
    """任务确认响应模型"""
    status: str = "success"
    message: str = "确认操作完成"


class TaskStatusUpdateRequest(BaseModel):
    """任务状态更新请求"""
    status: TaskStatus
