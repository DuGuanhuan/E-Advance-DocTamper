"""
案例库数据模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class CaseLibraryEntry(Base):
    """案例库条目模型"""
    __tablename__ = "case_library"
    
    case_id = Column(String(20), primary_key=True, index=True)
    source_task_id = Column(String(20), ForeignKey("audit_tasks.task_id"), nullable=False)
    
    # 伪造类型列表 (JSON格式存储，兼容SQLite)
    forgery_types = Column(JSON, nullable=True)
    
    # 审核员备注
    auditor_notes = Column(Text, nullable=True)
    
    # 标注区域坐标 (JSON格式: {"x": 100, "y": 150, "w": 200, "h": 50})
    bounding_box = Column(JSON, nullable=True)
    
    # 确认信息
    confirmed_by = Column(String(50), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    source_task = relationship("AuditTask", back_populates="case_entry")
    
    def __repr__(self):
        return f"<CaseLibraryEntry(case_id='{self.case_id}', confirmed_by='{self.confirmed_by}')>"
    
    @property
    def image_url(self):
        """获取案例图片URL"""
        if self.source_task and self.source_task.files:
            return self.source_task.files[0].file_url
        return None