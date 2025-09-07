"""
任务相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.task_service import TaskService
from app.services.file_service import FileService
from app.schemas.task import TaskCreateResponse, TaskDetailResponse, TaskListResponse
from app.models.task import TaskStatus
from loguru import logger

router = APIRouter()

@router.post("/tasks", response_model=TaskCreateResponse)
async def create_task(
    files: List[UploadFile] = File(...),
    assignee: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    创建新的审核任务并上传文件
    
    - **files**: 上传的文件列表（支持图片和PDF）
    - **assignee**: 指定的审核员（可选）
    """
    try:
        # 验证至少上传一个文件
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="至少需要上传一个文件")
        
        # 创建任务服务
        task_service = TaskService(db)
        file_service = FileService(db)
        
        # 创建任务
        task = task_service.create_task(assignee=assignee)
        
        # 保存文件
        saved_files = await file_service.save_multiple_files(files, task.task_id)
        
        logger.info(f"任务创建成功: {task.task_id}, 文件数量: {len(saved_files)}")
        
        return TaskCreateResponse(
            task_id=task.task_id,
            status=task.status,
            message=f"任务创建成功，已上传 {len(saved_files)} 个文件"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"任务创建失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    search_term: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    
    - **status**: 按状态筛选
    - **search_term**: 搜索任务ID或负责人
    - **page**: 页码
    - **page_size**: 每页数量
    """
    task_service = TaskService(db)
    return task_service.get_tasks(
        status=status,
        search_term=search_term,
        page=page,
        page_size=page_size
    )

@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task_detail(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务详情
    
    - **task_id**: 任务ID
    """
    task_service = TaskService(db)
    task_detail = task_service.get_task_detail(task_id)
    
    if not task_detail:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    return task_detail

@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: TaskStatus,
    db: Session = Depends(get_db)
):
    """
    更新任务状态
    
    - **task_id**: 任务ID
    - **status**: 新状态
    """
    task_service = TaskService(db)
    task = task_service.update_task_status(task_id, status)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    return {"message": f"任务 {task_id} 状态已更新为 {status}"}