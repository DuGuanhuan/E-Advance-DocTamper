"""
图片文件数据模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ImageFile(Base):
    """图片文件模型"""
    __tablename__ = "image_files"
    
    file_id = Column(String(20), primary_key=True, index=True)
    task_id = Column(String(20), ForeignKey("audit_tasks.task_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    task = relationship("AuditTask", back_populates="files")
    
    def __repr__(self):
        return f"<ImageFile(file_id='{self.file_id}', filename='{self.filename}')>"
    
    @property
    def file_url(self):
        """生成文件访问URL"""
        return f"/static/uploads/{self.file_path}"