"""
任务相关API路由 - 修复版本
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.task_service import TaskService
from app.services.file_service import FileService
from app.schemas.task import (
    TaskCreateResponse, TaskDetailResponse, TaskListResponse, 
    TaskConfirmRequest, TaskConfirmResponse
)
from app.core.constants import TaskStatus
from loguru import logger

router = APIRouter()

class TaskStatusUpdate(BaseModel):
    """任务状态更新模型"""
    status: TaskStatus

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
    search_term: Optional[str] = Query(None, description="搜索关键词（任务ID、负责人、文件名）"),
    assignee: Optional[str] = Query(None, description="负责人筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段（task_id, status, assignee, created_at, updated_at）"),
    sort_order: str = Query("desc", description="排序方向（asc, desc）"),
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    
    - **status**: 按状态筛选
    - **search_term**: 搜索任务ID、负责人或文件名
    - **assignee**: 按负责人筛选
    - **page**: 页码
    - **page_size**: 每页数量
    - **sort_by**: 排序字段
    - **sort_order**: 排序方向
    """
    task_service = TaskService(db)
    return task_service.get_tasks(
        status=status,
        search_term=search_term,
        assignee=assignee,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
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
    update_data: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    更新任务状态
    
    - **task_id**: 任务ID
    - **update_data**: 包含新状态、操作人、变更原因的请求体
    """
    task_service = TaskService(db)
    
    # 检查任务是否存在
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    # 更新任务状态
    updated_task = task_service.update_task_status(task_id, update_data.status)
    if not updated_task:
        raise HTTPException(status_code=400, detail=f"状态更新失败，可能是不允许的状态转换")
    
    return {"status": "success", "message": f"任务状态已更新为: {update_data.status}"}

@router.get("/tasks/{task_id}/status-history")
async def get_task_status_history(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务状态变更历史
    
    - **task_id**: 任务ID
    """
    task_service = TaskService(db)
    history = await task_service.get_task_status_history(task_id)
    
    return {
        "task_id": task_id,
        "status_history": [
            {
                "log_id": log.log_id,
                "old_status": log.old_status,
                "new_status": log.new_status,
                "changed_by": log.changed_by,
                "change_reason": log.change_reason,
                "created_at": log.created_at
            }
            for log in history
        ]
    }

@router.get("/tasks/{task_id}/allowed-transitions")
async def get_allowed_status_transitions(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务允许的状态转换
    
    - **task_id**: 任务ID
    """
    task_service = TaskService(db)
    transitions = task_service.get_allowed_status_transitions(task_id)
    
    return {
        "task_id": task_id,
        "allowed_transitions": [status.value for status in transitions]
    }

@router.post("/tasks/{task_id}/confirm", response_model=TaskConfirmResponse)
async def confirm_task(
    task_id: str,
    confirm_data: TaskConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    确认任务结果 - 根据PRD要求实现
    
    - **task_id**: 任务ID
    - **is_forgery**: true表示确认伪造，false表示标记为无风险
    - **forgery_types**: 伪造类型列表（当is_forgery为true时）
    - **notes**: 审核意见
    - **bounding_box**: 标注区域坐标
    """
    task_service = TaskService(db)
    
    # 检查任务是否存在
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    # 检查任务状态是否为pending_review
    if task.status != TaskStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=400, 
            detail=f"任务状态必须为pending_review才能确认，当前状态: {task.status}"
        )
    
    # 根据is_forgery确定新状态
    new_status = TaskStatus.CONFIRMED_FORGERY if confirm_data.is_forgery else TaskStatus.CONFIRMED_SAFE
    
    # 更新任务状态
    updated_task = task_service.update_task_status(task_id, new_status)
    if not updated_task:
        raise HTTPException(status_code=500, detail="状态更新失败")
    
    # TODO: 如果是确认伪造，需要归档到案例库
    # 这部分将在后续的案例库功能中实现
    
    action = "确认伪造" if confirm_data.is_forgery else "标记为无风险"
    logger.info(f"任务 {task_id} {action}完成，审核意见: {confirm_data.notes}")
    
    return TaskConfirmResponse(
        status="success",
        message=f"任务{action}完成"
    )