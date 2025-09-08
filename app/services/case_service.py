"""
案例库服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime

from app.models.case import CaseLibraryEntry
from app.models.task import AuditTask
from app.models.image import ImageFile
from loguru import logger


class CaseService:
    """案例库服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ---------- ID 生成 ----------
    def generate_case_id(self) -> str:
        """生成案例ID (CASE-001格式)"""
        all_cases = self.db.query(CaseLibraryEntry.case_id).filter(
            CaseLibraryEntry.case_id.like("CASE-%")
        ).all()

        max_num = 0
        for case_record in all_cases:
            case_id = case_record[0]
            try:
                num = int(case_id.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue

        new_num = max_num + 1
        return f"CASE-{new_num:03d}"

    # ---------- 创建/归档 ----------
    def create_case_from_task(
        self,
        task_id: str,
        forgery_types: Optional[List[str]] = None,
        bounding_boxes: Optional[List[Dict[str, int]]] = None,
        notes: Optional[str] = None,
        confirmed_by: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> Optional[CaseLibraryEntry]:
        """从任务创建案例记录

        说明：为兼容既有表结构（无迁移），将多框标注与置信度一起存入 bounding_box JSON 字段。
        """
        task = self.db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
        if not task:
            logger.error(f"归档失败，任务不存在: {task_id}")
            return None

        case_id = self.generate_case_id()

        # 兼容字段：将多框与置信度放入一个JSON对象中存到原有的 bounding_box 字段
        bbox_payload: Dict[str, Any] = None
        if bounding_boxes or confidence_score is not None:
            bbox_payload = {
                "boxes": bounding_boxes or [],
                "confidence_score": confidence_score,
            }

        entry = CaseLibraryEntry(
            case_id=case_id,
            source_task_id=task_id,
            forgery_types=forgery_types or [],
            auditor_notes=notes,
            bounding_box=bbox_payload,  # 兼容字段名
            confirmed_by=confirmed_by or "system",
        )

        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(f"任务 {task_id} 已归档为案例 {case_id}")
        return entry

    # ---------- 查询 ----------
    def get_cases(
        self,
        forgery_type: Optional[str] = None,
        search_term: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """获取案例列表，支持筛选、搜索、分页"""
        from sqlalchemy.orm import joinedload

        query = self.db.query(CaseLibraryEntry).options(
            joinedload(CaseLibraryEntry.source_task).joinedload(AuditTask.files)
        )

        # 时间范围
        if date_from:
            query = query.filter(CaseLibraryEntry.confirmed_at >= date_from)
        if date_to:
            query = query.filter(CaseLibraryEntry.confirmed_at <= date_to)

        # 伪造类型（JSON文本模糊匹配，SQLite简化）
        if forgery_type:
            query = query.filter(CaseLibraryEntry.forgery_types.like(f'%"{forgery_type}"%'))

        # 搜索（案例ID、任务ID、文件名、备注）
        if search_term:
            query = query.outerjoin(CaseLibraryEntry.source_task).outerjoin(ImageFile).filter(
                or_(
                    CaseLibraryEntry.case_id.contains(search_term),
                    CaseLibraryEntry.source_task_id.contains(search_term),
                    ImageFile.filename.contains(search_term),
                    CaseLibraryEntry.auditor_notes.contains(search_term),
                )
            ).distinct()

        # 统计总数
        total = query.count()

        # 排序字段
        if sort_by == "case_id":
            order_column = CaseLibraryEntry.case_id
        elif sort_by == "confirmed_at":
            order_column = CaseLibraryEntry.confirmed_at
        else:
            order_column = CaseLibraryEntry.confirmed_at

        if sort_order.lower() == "asc":
            query = query.order_by(order_column)
        else:
            query = query.order_by(desc(order_column))

        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_case_detail(self, case_id: str) -> Optional[CaseLibraryEntry]:
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(CaseLibraryEntry)
            .options(joinedload(CaseLibraryEntry.source_task).joinedload(AuditTask.files))
            .filter(CaseLibraryEntry.case_id == case_id)
            .first()
        )

    def get_case_statistics(self) -> Dict[str, Any]:
        """简单统计：总数、按类型计数（基于JSON文本扫描）"""
        total = self.db.query(CaseLibraryEntry).count()

        # 统计按类型分布（简化：遍历统计）
        by_type: Dict[str, int] = {}
        for entry in self.db.query(CaseLibraryEntry).all():
            types = entry.forgery_types or []
            for t in types:
                by_type[t] = by_type.get(t, 0) + 1

        return {"total": total, "by_type": by_type}

    def search_similar_cases(self, image_hash: str) -> List[CaseLibraryEntry]:
        """相似案例检索（占位实现）"""
        logger.warning("search_similar_cases 为占位实现，未接入相似度检索")
        return []

