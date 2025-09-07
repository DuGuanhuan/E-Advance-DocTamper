"""
案例库相关Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class CaseItem(BaseModel):
    case_id: str
    source_task_id: str
    image_url: Optional[str] = None
    filename: Optional[str] = None
    forgery_types: List[str] = Field(default_factory=list)
    reviewer_notes: Optional[str] = None
    confidence_score: Optional[float] = None
    confirmed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    items: List[CaseItem]
    total: int
    page: int
    page_size: int


class CaseDetail(BaseModel):
    case_id: str
    source_task_id: str
    image_url: Optional[str] = None
    filename: Optional[str] = None
    forgery_types: List[str] = Field(default_factory=list)
    reviewer_notes: Optional[str] = None
    confidence_score: Optional[float] = None
    bounding_boxes: List[Dict[str, float]] = Field(default_factory=list)
    confirmed_by: Optional[str] = None
    confirmed_at: datetime


class CaseStatistics(BaseModel):
    total: int
    by_type: Dict[str, int]


class ForgeryTypeItem(BaseModel):
    value: str
    label: str
