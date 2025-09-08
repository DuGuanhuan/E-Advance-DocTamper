"""
分析报告相关的Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from typing import ForwardRef


class ImageInfo(BaseModel):
    """图片信息模型"""
    url: str
    filename: str


class HistoricalMatch(BaseModel):
    """历史匹配图片模型"""
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="相似度分数，范围0.0-1.0")
    image: ImageInfo


class AnalysisReportData(BaseModel):
    """分析报告数据模型"""
    task_id: str
    detection_timestamp: datetime
    current_image: ImageInfo
    historical_match: Optional[HistoricalMatch] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisReportResponse(BaseModel):
    """分析报告响应模型"""
    success: bool = True
    data: AnalysisReportData


class AnalysisDetailItem(BaseModel):
    """分析详情项模型"""
    label: str
    content: str
    is_risk: bool = False  # 是否为风险项


class AnalysisDetailsResponse(BaseModel):
    """分析详情响应模型"""
    task_id: str
    details: list[AnalysisDetailItem]