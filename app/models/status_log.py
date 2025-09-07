"""
状态变更日志模型
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class StatusLog(Base):
    """状态变更日志表"""
    __tablename__ = "status_logs"
    
    log_id = Column(String(20), primary_key=True, index=True)
    task_id = Column(String(20), ForeignKey("audit_tasks.task_id"), nullable=False)
    old_status = Column(String(20), nullable=True)  # 旧状态，首次创建时为空
    new_status = Column(String(20), nullable=False)  # 新状态
    changed_by = Column(String(50), nullable=True)   # 操作人
    change_reason = Column(Text, nullable=True)      # 变更原因
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    task = relationship("AuditTask", back_populates="status_logs")