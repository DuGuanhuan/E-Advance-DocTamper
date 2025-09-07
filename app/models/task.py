"""
审核任务数据模型
"""
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.constants import TaskStatus

class AuditTask(Base):
    """审核任务模型"""
    __tablename__ = "audit_tasks"
    
    task_id = Column(String(20), primary_key=True, index=True)
    status = Column(String(20), default=TaskStatus.PROCESSING.value, nullable=False)
    assignee = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    files = relationship("ImageFile", back_populates="task", cascade="all, delete-orphan")
    analysis_result = relationship("AnalysisResult", back_populates="task", uselist=False)
    case_entry = relationship("CaseLibraryEntry", back_populates="source_task", uselist=False)
    status_logs = relationship("StatusLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AuditTask(task_id='{self.task_id}', status='{self.status}')>"