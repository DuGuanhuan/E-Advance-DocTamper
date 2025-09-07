"""
分析结果数据模型
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AnalysisResult(Base):
    """分析结果模型"""
    __tablename__ = "analysis_results"
    
    result_id = Column(String(20), primary_key=True, index=True)
    task_id = Column(String(20), ForeignKey("audit_tasks.task_id"), nullable=False)
    
    # AI检测结果 (JSON格式存储)
    ai_findings = Column(JSON, nullable=True)
    
    # 历史相似图片匹配结果 (JSON格式存储)
    historical_matches = Column(JSON, nullable=True)
    
    # 风险评分 (0.0-1.0)
    risk_score = Column(Float, nullable=True)
    
    # 检测发现描述
    findings_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    task = relationship("AuditTask", back_populates="analysis_result")
    
    def __repr__(self):
        return f"<AnalysisResult(result_id='{self.result_id}', task_id='{self.task_id}')>"