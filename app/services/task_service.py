"""
任务管理服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.task import AuditTask
from app.models.image import ImageFile
from app.core.constants import TaskStatus, TaskStatusTransition
from app.schemas.task import (
    TaskCreateResponse, TaskDetailResponse, TaskListResponse, 
    ImageFileResponse, HistoricalMatch, AIFinding, AnalysisResult
)
from loguru import logger

class TaskService:
    """任务管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_task_id(self) -> str:
        """生成任务ID (TSK-001格式)"""
        # 查询所有任务ID，找到最大编号
        all_tasks = self.db.query(AuditTask.task_id).filter(
            AuditTask.task_id.like("TSK-%")
        ).all()
        
        max_num = 0
        for task_record in all_tasks:
            task_id = task_record[0]
            try:
                num = int(task_id.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
        
        new_num = max_num + 1
        return f"TSK-{new_num:03d}"
    
    def create_task(self, assignee: Optional[str] = None) -> AuditTask:
        """创建新的审核任务"""
        task_id = self.generate_task_id()
        
        task = AuditTask(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            assignee=assignee or "系统自动分配"
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"创建新任务: {task_id}")
        return task
    
    def get_task(self, task_id: str) -> Optional[AuditTask]:
        """根据ID获取任务"""
        from sqlalchemy.orm import joinedload
        return self.db.query(AuditTask).options(joinedload(AuditTask.files)).filter(AuditTask.task_id == task_id).first()
    
    def get_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        search_term: Optional[str] = None,
        assignee: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> TaskListResponse:
        """获取任务列表"""
        from sqlalchemy.orm import joinedload
        query = self.db.query(AuditTask).options(joinedload(AuditTask.files))
        
        # 状态筛选
        if status:
            query = query.filter(AuditTask.status == status)
        
        # 负责人筛选
        if assignee:
            query = query.filter(AuditTask.assignee.contains(assignee))
        
        # 关键词搜索（搜索任务ID、负责人、关联文件名）
        if search_term:
            query = query.outerjoin(ImageFile).filter(
                or_(
                    AuditTask.task_id.contains(search_term),
                    AuditTask.assignee.contains(search_term),
                    ImageFile.filename.contains(search_term)
                )
            ).distinct()
        
        # 总数统计
        total = query.count()
        
        # 排序
        if sort_by == "task_id":
            order_column = AuditTask.task_id
        elif sort_by == "status":
            order_column = AuditTask.status
        elif sort_by == "assignee":
            order_column = AuditTask.assignee
        elif sort_by == "updated_at":
            order_column = AuditTask.updated_at
        else:  # 默认按创建时间
            order_column = AuditTask.created_at
        
        if sort_order.lower() == "asc":
            query = query.order_by(order_column)
        else:
            query = query.order_by(desc(order_column))
        
        # 分页
        offset = (page - 1) * page_size
        tasks = query.offset(offset).limit(page_size).all()
        
        return TaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size
        )
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[AuditTask]:
        """更新任务状态 - 根据PRD要求添加状态转换验证"""
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return None
        
        # 检查状态转换是否允许
        if not TaskStatusTransition.can_transition(task.status, status):
            logger.error(f"不允许的状态转换: {task.status} -> {status}")
            return None
        
        old_status = task.status
        task.status = status
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"任务 {task_id} 状态更新: {old_status} -> {status}")
        return task
    
    def get_task_detail(self, task_id: str) -> Optional[TaskDetailResponse]:
        """获取任务详情（包含文件列表和分析结果）"""
        task = self.db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
        if not task:
            return None
        
        # 计算文件统计信息
        total_file_size = sum(f.file_size or 0 for f in task.files)
        file_count = len(task.files)
        
        # 获取第一个上传的图片作为主图片
        uploaded_image = None
        if task.files:
            first_file = task.files[0]
            uploaded_image = {
                "filename": first_file.filename,
                "url": first_file.file_url
            }
        
        # 生成分析结果（模拟数据）
        analysis_result = self._generate_analysis_result(task_id)
        
        return TaskDetailResponse(
            task_id=task.task_id,
            status=task.status,
            assignee=task.assignee,
            created_at=task.created_at,
            updated_at=task.updated_at,
            files=[
                ImageFileResponse(
                    file_id=f.file_id,
                    filename=f.filename,
                    file_size=f.file_size,
                    mime_type=f.mime_type,
                    file_url=f"/static/uploads/{f.file_path}",
                    created_at=f.created_at
                )
                for f in task.files
            ],
            file_count=file_count,
            total_file_size=total_file_size,
            uploaded_image=uploaded_image,
            analysis_result=analysis_result
        )
    
    def get_task_stats(self) -> dict:
        """获取任务统计信息"""
        total_tasks = self.db.query(AuditTask).count()
        
        stats = {
            "total_tasks": total_tasks,
            "processing_count": self.db.query(AuditTask).filter(AuditTask.status == TaskStatus.PROCESSING).count(),
            "pending_review_count": self.db.query(AuditTask).filter(AuditTask.status == TaskStatus.PENDING_REVIEW).count(),
            "confirmed_forgery_count": self.db.query(AuditTask).filter(AuditTask.status == TaskStatus.CONFIRMED_FORGERY).count(),
            "confirmed_safe_count": self.db.query(AuditTask).filter(AuditTask.status == TaskStatus.CONFIRMED_SAFE).count(),
        }
        
        return stats
    
    async def update_task_status_with_log(
        self,
        task_id: str,
        new_status: TaskStatus,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> bool:
        """
        更新任务状态并记录日志
        
        Args:
            task_id: 任务ID
            new_status: 新状态
            changed_by: 操作人
            change_reason: 变更原因
            
        Returns:
            bool: 是否更新成功
        """
        return await StatusService.update_task_status(
            self.db, task_id, new_status, changed_by, change_reason
        )
    
    async def get_task_status_history(self, task_id: str):
        """获取任务状态变更历史"""
        return await StatusService.get_status_history(self.db, task_id)
    
    def get_allowed_status_transitions(self, task_id: str) -> List[TaskStatus]:
        """获取任务允许的状态转换"""
        task = self.get_task(task_id)
        if not task:
            return []
        
        return TaskStatusTransition.get_allowed_transitions(task.status)
    
    def _generate_analysis_result(self, task_id: str) -> AnalysisResult:
        """生成分析结果（模拟数据）"""
        # 根据任务ID生成不同的模拟数据
        historical_matches = []
        ai_findings = []
        
        # 根据任务ID的后缀数字决定相似度
        try:
            task_num = int(task_id.split('-')[1])
        except (IndexError, ValueError):
            task_num = 1
        
        # 生成历史匹配数据
        if task_num % 3 == 1:  # 高相似度案例
            historical_matches = [
                HistoricalMatch(
                    filename="INV202408015.jpg",
                    url="/static/uploads/historical_sample.jpg",
                    similarity=0.986,  # 98.6%
                    diff_details="发现相似图片 (相似度 98.6%)，存在 3 处关键信息不一致。"
                )
            ]
            ai_findings = [
                AIFinding(
                    type="AI篡改痕迹检测",
                    detail="在金额 '￥8,500.00' 区域检测到像素级别涂抹与二次填充痕迹。"
                ),
                AIFinding(
                    type="文字链一致性分析",
                    detail="'捌仟伍佰元整' 与数字金额 '8,500.00' 不符，原始OCR识别可能为 '3,500.00'。"
                ),
                AIFinding(
                    type="元数据(EXIF)分析",
                    detail="修改软件为 Adobe Photoshop 23.0。"
                )
            ]
        elif task_num % 3 == 2:  # 中等相似度案例
            historical_matches = [
                HistoricalMatch(
                    filename="INV202407022.jpg",
                    url="/static/uploads/historical_sample.jpg",
                    similarity=0.923,  # 92.3%
                    diff_details="发现相似图片 (相似度 92.3%)，存在 1 处关键信息不一致。"
                )
            ]
            ai_findings = [
                AIFinding(
                    type="AI篡改痕迹检测",
                    detail="未检测到明显篡改痕迹。"
                ),
                AIFinding(
                    type="文字一致性分析",
                    detail="文字内容基本一致，无明显异常。"
                ),
                AIFinding(
                    type="元数据(EXIF)分析",
                    detail="文件元数据正常，无编辑软件痕迹。"
                )
            ]
        else:  # 低相似度或无匹配案例
            # 相似度低于90%，不显示历史匹配
            historical_matches = [
                HistoricalMatch(
                    filename="INV202406010.jpg",
                    url="/static/uploads/historical_sample.jpg",
                    similarity=0.756,  # 75.6% - 低于阈值
                    diff_details="发现相似图片 (相似度 75.6%)，相似度较低。"
                )
            ]
            ai_findings = [
                AIFinding(
                    type="AI篡改痕迹检测",
                    detail="未检测到篡改痕迹，图像质量良好。"
                ),
                AIFinding(
                    type="元数据(EXIF)分析",
                    detail="文件元数据正常，拍摄设备信息完整。"
                )
            ]
        
        return AnalysisResult(
            historical_matches=historical_matches,
            ai_findings=ai_findings
        )