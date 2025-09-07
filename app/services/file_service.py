"""
文件管理服务
"""
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from PIL import Image
import aiofiles
import os
import uuid
from typing import List, Optional
import mimetypes

from app.models.image import ImageFile
from app.core.config import settings
from loguru import logger

class FileService:
    """文件管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_file_id(self) -> str:
        """生成文件ID (FILE-001格式)"""
        # 查询所有文件ID，找到最大编号
        all_files = self.db.query(ImageFile.file_id).filter(
            ImageFile.file_id.like("FILE-%")
        ).all()
        
        max_num = 0
        for file_record in all_files:
            file_id = file_record[0]
            try:
                num = int(file_id.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
        
        new_num = max_num + 1
        return f"FILE-{new_num:03d}"
    
    def validate_file(self, file: UploadFile) -> bool:
        """验证文件类型和大小"""
        # 检查文件类型
        if file.content_type not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}. 支持的类型: {settings.allowed_file_types}"
            )
        
        # 检查文件大小（这里只是基础检查，实际大小在保存时检查）
        return True
    
    async def save_file(self, file: UploadFile, task_id: str) -> ImageFile:
        """保存上传的文件"""
        # 验证文件
        self.validate_file(file)
        
        # 生成文件ID和路径
        file_id = self.generate_file_id()
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{file_id}_{task_id}{file_extension}"
        file_path = os.path.join(settings.upload_dir, safe_filename)
        
        # 确保上传目录存在
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # 保存文件
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(1024):
                file_size += len(chunk)
                
                # 检查文件大小
                if file_size > settings.max_file_size:
                    # 删除已保存的部分文件
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件大小超过限制: {settings.max_file_size} bytes"
                    )
                
                await f.write(chunk)
        
        # 重置文件指针
        await file.seek(0)
        
        # 创建数据库记录
        image_file = ImageFile(
            file_id=file_id,
            task_id=task_id,
            filename=file.filename,
            file_path=safe_filename,
            file_size=file_size,
            mime_type=file.content_type
        )
        
        self.db.add(image_file)
        self.db.commit()
        self.db.refresh(image_file)
        
        logger.info(f"文件保存成功: {file_id} -> {file_path}")
        return image_file
    
    async def save_multiple_files(self, files: List[UploadFile], task_id: str) -> List[ImageFile]:
        """批量保存文件"""
        saved_files = []
        
        for file in files:
            try:
                saved_file = await self.save_file(file, task_id)
                saved_files.append(saved_file)
            except Exception as e:
                # 如果某个文件保存失败，清理已保存的文件
                for saved_file in saved_files:
                    await self.delete_file(saved_file.file_id)
                raise e
        
        return saved_files
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        file_record = self.db.query(ImageFile).filter(ImageFile.file_id == file_id).first()
        if not file_record:
            return False
        
        # 删除物理文件
        file_path = os.path.join(settings.upload_dir, file_record.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 删除数据库记录
        self.db.delete(file_record)
        self.db.commit()
        
        logger.info(f"文件删除成功: {file_id}")
        return True
    
    def get_file(self, file_id: str) -> Optional[ImageFile]:
        """获取文件信息"""
        return self.db.query(ImageFile).filter(ImageFile.file_id == file_id).first()
    
    def get_files_by_task(self, task_id: str) -> List[ImageFile]:
        """获取任务的所有文件"""
        return self.db.query(ImageFile).filter(ImageFile.task_id == task_id).all()
    
    async def create_thumbnail(self, file_path: str, thumbnail_path: str, size: tuple = (200, 200)):
        """创建图片缩略图"""
        try:
            with Image.open(file_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, optimize=True, quality=85)
                logger.info(f"缩略图创建成功: {thumbnail_path}")
        except Exception as e:
            logger.error(f"缩略图创建失败: {e}")
            raise e