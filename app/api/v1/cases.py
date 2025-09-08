"""
案例库相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.case_service import CaseService
from app.schemas.case import (
    CaseListResponse, CaseItem, CaseDetail, CaseStatistics, ForgeryTypeItem
)
from app.core.constants import ForgeryType

router = APIRouter()


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    forgery_type: Optional[str] = Query(None, description="伪造类型筛选"),
    search_term: Optional[str] = Query(None, description="搜索关键词"),
    date_from: Optional[str] = Query(None, description="开始时间，ISO格式"),
    date_to: Optional[str] = Query(None, description="结束时间，ISO格式"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("confirmed_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):
    service = CaseService(db)

    # 解析时间
    from datetime import datetime
    df = datetime.fromisoformat(date_from) if date_from else None
    dt = datetime.fromisoformat(date_to) if date_to else None

    result = service.get_cases(
        forgery_type=forgery_type,
        search_term=search_term,
        date_from=df,
        date_to=dt,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items: list[CaseItem] = []
    for entry in result["items"]:
        # 提取图片与文件名
        image_url = None
        filename = None
        if entry.source_task and entry.source_task.files:
            image_url = entry.source_task.files[0].file_url
            filename = entry.source_task.files[0].filename

        # 从兼容字段中取出置信度与标注框
        confidence = None
        if isinstance(entry.bounding_box, dict):
            confidence = entry.bounding_box.get("confidence_score")

        items.append(
            CaseItem(
                case_id=entry.case_id,
                source_task_id=entry.source_task_id,
                image_url=image_url,
                filename=filename,
                forgery_types=entry.forgery_types or [],
                reviewer_notes=entry.auditor_notes,
                confidence_score=confidence,
                confirmed_at=entry.confirmed_at,
            )
        )

    return CaseListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )

@router.get("/cases/statistics", response_model=CaseStatistics)
async def case_statistics(
    db: Session = Depends(get_db)
):
    service = CaseService(db)
    stats = service.get_case_statistics()
    return CaseStatistics(**stats)


@router.get("/cases/forgery-types", response_model=list[ForgeryTypeItem])
async def forgery_types():
    # 使用现有常量（值为中文标签），前端按需展示
    return [
        ForgeryTypeItem(value=item.value, label=item.value) for item in ForgeryType
    ]


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def case_detail(
    case_id: str,
    db: Session = Depends(get_db)
):
    service = CaseService(db)
    entry = service.get_case_detail(case_id)
    if not entry:
        raise HTTPException(status_code=404, detail="案例不存在")

    image_url = None
    filename = None
    if entry.source_task and entry.source_task.files:
        image_url = entry.source_task.files[0].file_url
        filename = entry.source_task.files[0].filename

    boxes = []
    confidence = None
    if isinstance(entry.bounding_box, dict):
        boxes = entry.bounding_box.get("boxes") or []
        confidence = entry.bounding_box.get("confidence_score")

    return CaseDetail(
        case_id=entry.case_id,
        source_task_id=entry.source_task_id,
        image_url=image_url,
        filename=filename,
        forgery_types=entry.forgery_types or [],
        reviewer_notes=entry.auditor_notes,
        confidence_score=confidence,
        bounding_boxes=boxes,
        confirmed_by=entry.confirmed_by,
        confirmed_at=entry.confirmed_at,
    )
