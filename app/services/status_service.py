"""
状态管理服务
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import AuditTask, StatusLog
from app.core.constants import TaskStatus, STATUS_TRANSITIONS
from app.core.database import get_db
from loguru import logger


class StatusService:
    """状态管理服务类"""
    
    @staticmethod
    async def validate_status_transition(
        current_status: TaskStatus, 
        new_status: TaskStatus
    ) -> bool:
        """
        验证状态转换是否合法
        
        Args:
            current_status: 当前状态
            new_status: 目标状态
            
        Returns:
            bool: 是否允许转换
        """
        if current_status == new_status:
            return True
            
        allowed_transitions = STATUS_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions
    
    @staticmethod
    async def generate_log_id(db: AsyncSession) -> str:
        """生成状态日志ID"""
        result = await db.execute(select(StatusLog.log_id))
        existing_ids = [row[0] for row in result.fetchall()]
        
        if not existing_ids:
            return "LOG-001"
        
        # 提取数字部分并找到最大值
        max_num = 0
        for log_id in existing_ids:
            try:
                num = int(log_id.split('-')[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
        
        return f"LOG-{max_num + 1:03d}"
    
    @staticmethod
    async def update_task_status(
        db: AsyncSession,
        task_id: str,
        new_status: TaskStatus,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> bool:
        """
        更新任务状态并记录日志
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            new_status: 新状态
            changed_by: 操作人
            change_reason: 变更原因
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取当前任务
            result = await db.execute(
                select(AuditTask).where(AuditTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return False
            
            old_status = task.status
            
            # 验证状态转换
            if not await StatusService.validate_status_transition(old_status, new_status):
                logger.error(f"非法状态转换: {old_status} -> {new_status}")
                return False
            
            # 更新任务状态
            task.status = new_status
            
            # 创建状态变更日志
            log_id = await StatusService.generate_log_id(db)
            status_log = StatusLog(
                log_id=log_id,
                task_id=task_id,
                old_status=old_status.value if old_status else None,
                new_status=new_status.value,
                changed_by=changed_by,
                change_reason=change_reason
            )
            
            db.add(status_log)
            await db.commit()
            
            logger.info(f"任务状态更新成功: {task_id} {old_status} -> {new_status}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"状态更新失败: {e}")
            return False
    
    @staticmethod
    async def get_status_history(
        db: AsyncSession,
        task_id: str
    ) -> List[StatusLog]:
        """
        获取任务状态变更历史
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            List[StatusLog]: 状态变更历史列表
        """
        result = await db.execute(
            select(StatusLog)
            .where(StatusLog.task_id == task_id)
            .order_by(StatusLog.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_allowed_transitions(
        current_status: TaskStatus
    ) -> List[TaskStatus]:
        """
        获取当前状态允许的转换状态
        
        Args:
            current_status: 当前状态
            
        Returns:
            List[TaskStatus]: 允许转换的状态列表
        """
        return STATUS_TRANSITIONS.get(current_status, [])