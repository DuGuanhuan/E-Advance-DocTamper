"""
状态管理服务（同步版本）
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import AuditTask, StatusLog
from app.core.constants import TaskStatus, TaskStatusTransition
from loguru import logger


class StatusService:
    """状态管理服务类（同步SQLAlchemy会话）"""

    @staticmethod
    def validate_status_transition(
        current_status: TaskStatus | str,
        new_status: TaskStatus,
    ) -> bool:
        """验证状态转换是否合法"""
        if isinstance(current_status, str):
            try:
                current_status = TaskStatus(current_status)
            except Exception:
                return False
        if current_status == new_status:
            return True
        return TaskStatusTransition.can_transition(current_status, new_status)

    @staticmethod
    def generate_log_id(db: Session) -> str:
        """生成状态日志ID (LOG-001 递增)"""
        rows = db.query(StatusLog.log_id).all()
        if not rows:
            return "LOG-001"

        max_num = 0
        for (log_id,) in rows:
            try:
                num = int(str(log_id).split("-")[1])
                max_num = max(max_num, num)
            except Exception:
                continue
        return f"LOG-{max_num + 1:03d}"

    @staticmethod
    def update_task_status(
        db: Session,
        task_id: str,
        new_status: TaskStatus,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> bool:
        """更新任务状态并记录状态日志"""
        try:
            task = db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return False

            old_status = task.status
            if not StatusService.validate_status_transition(old_status, new_status):
                logger.error(f"非法状态转换: {old_status} -> {new_status}")
                return False

            # 更新任务
            task.status = new_status.value

            # 写入状态日志
            log_id = StatusService.generate_log_id(db)
            # 规范化日志中的状态字符串
            old_status_value = (
                old_status.value if isinstance(old_status, TaskStatus) else str(old_status)
            )
            new_status_value = new_status.value

            status_log = StatusLog(
                log_id=log_id,
                task_id=task_id,
                old_status=old_status_value,
                new_status=new_status_value,
                changed_by=changed_by,
                change_reason=change_reason,
            )
            db.add(status_log)
            db.commit()

            logger.info(f"任务状态更新成功: {task_id} {old_status} -> {new_status}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"状态更新失败: {e}")
            return False

    @staticmethod
    def get_status_history(db: Session, task_id: str) -> List[StatusLog]:
        """获取任务状态变更历史（按时间倒序）"""
        return (
            db.query(StatusLog)
            .filter(StatusLog.task_id == task_id)
            .order_by(desc(StatusLog.created_at))
            .all()
        )

    @staticmethod
    def get_allowed_transitions(current_status: TaskStatus | str) -> List[TaskStatus]:
        """获取当前状态允许的转换目标状态"""
        if isinstance(current_status, str):
            try:
                current_status = TaskStatus(current_status)
            except Exception:
                return []
        return TaskStatusTransition.get_allowed_transitions(current_status)
