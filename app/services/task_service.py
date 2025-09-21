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
from app.services.status_service import StatusService
from app.services.ai_integration_service import ai_service

class TaskService:
    """任务管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def start_ai_detection(self, task_id: str, image_path: str) -> bool:
        """
        启动AI检测流程
        
        Args:
            task_id: 任务ID
            image_path: 图像文件路径
            
        Returns:
            是否启动成功
        """
        try:
            logger.info(f"启动AI检测: 任务{task_id}, 图片{image_path}")
            
            # 调用AI集成服务进行检测
            ai_result = await ai_service.analyze_image_complete(image_path, task_id)
            
            # 保存AI检测结果到数据库
            await self._save_ai_detection_result(task_id, ai_result)
            
            # 更新任务状态为待审核
            self.update_task_status(task_id, TaskStatus.PENDING_REVIEW)
            
            logger.info(f"AI检测完成: 任务{task_id}")
            return True
            
        except Exception as e:
            logger.error(f"AI检测失败: 任务{task_id}, 错误: {e}")
            # 更新任务状态为失败
            self.update_task_status(task_id, TaskStatus.FAILED)
            return False
    
    async def _save_ai_detection_result(self, task_id: str, ai_result: dict):
        """保存AI检测结果到数据库"""
        try:
            # 查找或创建分析结果记录
            from app.models.analysis import AnalysisResult as AnalysisResultModel
            
            analysis_record = self.db.query(AnalysisResultModel).filter(
                AnalysisResultModel.task_id == task_id
            ).first()
            
            if not analysis_record:
                analysis_record = AnalysisResultModel(
                    task_id=task_id,
                    created_at=datetime.now()
                )
                self.db.add(analysis_record)
            
            # 更新AI检测结果
            analysis_record.ai_detection_result = ai_result
            analysis_record.confidence_score = ai_result.get("overall_risk_score", 0.0)
            analysis_record.processing_time = ai_result.get("processing_time", 0.0)
            analysis_record.updated_at = datetime.now()
            
            self.db.commit()
            logger.info(f"AI检测结果已保存: 任务{task_id}")
            
        except Exception as e:
            logger.error(f"保存AI检测结果失败: {e}")
            self.db.rollback()
            raise
    
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
            status=TaskStatus.PROCESSING.value,
            assignee=assignee or "系统自动分配"
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"创建新任务: {task_id}")
        return task

    async def process_exif_after_upload(self, task_id: str, image_relative_path: str) -> None:
        """在上传完成后执行 EXIF 分析，保存结果并切换状态为待核对"""
        try:
            # 物理路径：上传目录在 settings.upload_dir 下，ImageFile.file_path 已含文件名
            from app.core.config import settings
            import os
            image_path = os.path.join(settings.upload_dir, image_relative_path)

            exif_result = await ai_service.analyze_exif(image_path)

            # 简化展示：始终输出一行。命中编辑软件 → 显示软件；否则输出未检测到编辑软件
            findings = []
            software = (exif_result or {}).get("software")
            tampered_by_software = False
            for ind in (exif_result.get("risk_indicators") or []):
                desc = (ind.get("description") or "").lower()
                if desc.startswith("detected editing software"):
                    tampered_by_software = True
                    # 若 software 为空，尝试从描述提取
                    if not software:
                        try:
                            software = ind.get("description").split(":", 1)[1].strip()
                        except Exception:
                            pass
                    break

            if tampered_by_software and software:
                findings = [AIFinding(type="EXIF", detail=f"检测到编辑软件：{software}")]
            else:
                findings = [AIFinding(type="EXIF", detail="图片元数据：未检测到编辑软件信息")]

            # 保存到 AnalysisResult 表（合并到 ai_findings JSON）
            from app.models.analysis import AnalysisResult as AnalysisResultModel
            ar = (
                self.db.query(AnalysisResultModel)
                .filter(AnalysisResultModel.task_id == task_id)
                .first()
            )
            if not ar:
                # 生成 result_id
                result_id = self._generate_result_id()
                ar = AnalysisResultModel(result_id=result_id, task_id=task_id, ai_findings=[])
                self.db.add(ar)

            # 覆盖为简化后的单行（或空）
            ar.ai_findings = [{"type": f.type, "detail": f.detail} for f in findings]
            self.db.commit()
            self.db.refresh(ar)

            # 切换任务状态为待核对（写入日志）
            self.update_task_status_with_log(task_id, TaskStatus.PENDING_REVIEW)
        except Exception as e:
            logger.error(f"任务 {task_id} EXIF 处理失败: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            # 失败时也尝试置为待核对，避免卡在处理中
            try:
                self.update_task_status_with_log(task_id, TaskStatus.PENDING_REVIEW)
            except Exception:
                pass
    
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
        current = task.status
        try:
            current_enum = TaskStatus(current) if isinstance(current, str) else current
        except Exception:
            current_enum = TaskStatus.PROCESSING
        if not TaskStatusTransition.can_transition(current_enum, status):
            logger.error(f"不允许的状态转换: {task.status} -> {status}")
            return None
        
        old_status = task.status
        task.status = status.value
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"任务 {task_id} 状态更新: {old_status} -> {status}")
        return task
    
    def get_task_detail(self, task_id: str) -> Optional[TaskDetailResponse]:
        """获取任务详情（包含文件列表和分析结果）"""
        task = self.get_task(task_id)
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
        
        # 优先使用数据库中已有的 AI/EXIF 结果
        db_findings: Optional[list] = None
        try:
            from app.models.analysis import AnalysisResult as AnalysisResultModel
            ar = (
                self.db.query(AnalysisResultModel)
                .filter(AnalysisResultModel.task_id == task_id)
                .first()
            )
            if ar and ar.ai_findings:
                db_findings = ar.ai_findings
        except Exception:
            db_findings = None

        if db_findings:
            analysis_result = AnalysisResult(
                historical_matches=[],
                ai_findings=[AIFinding(type=it.get("type", "EXIF"), detail=it.get("detail", "")) for it in db_findings]
            )
        else:
            # 回退到模拟数据
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

    def _generate_result_id(self) -> str:
        """生成分析结果ID (RES-001 格式)"""
        from app.models.analysis import AnalysisResult as AnalysisResultModel
        rows = self.db.query(AnalysisResultModel.result_id).filter(
            AnalysisResultModel.result_id.like("RES-%")
        ).all()
        max_num = 0
        for (rid,) in rows:
            try:
                n = int(str(rid).split("-")[1])
                max_num = max(max_num, n)
            except Exception:
                continue
        return f"RES-{max_num + 1:03d}"
    
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
    
    def update_task_status_with_log(
        self,
        task_id: str,
        new_status: TaskStatus,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> bool:
        """同步版本：更新任务状态并记录日志"""
        return StatusService.update_task_status(
            self.db, task_id, new_status, changed_by, change_reason
        )
    
    def get_task_status_history(self, task_id: str):
        """获取任务状态变更历史（同步）"""
        return StatusService.get_status_history(self.db, task_id)
    
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
