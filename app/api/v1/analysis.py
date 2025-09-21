"""
分析报告API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisReportResponse, AnalysisDetailsResponse
from loguru import logger

router = APIRouter()


@router.get("/analysis-report/{task_id}", response_model=AnalysisReportResponse)
async def get_analysis_report(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取分析报告
    
    - **task_id**: 任务ID
    """
    try:
        analysis_service = AnalysisService(db)
        report_data = analysis_service.get_analysis_report(task_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail=f"报告不存在: {task_id}")
        
        return AnalysisReportResponse(
            success=True,
            data=report_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析报告失败: {str(e)}")


@router.get("/analysis-details/{task_id}", response_model=AnalysisDetailsResponse)
async def get_analysis_details(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取分析详情
    
    - **task_id**: 任务ID
    """
    try:
        analysis_service = AnalysisService(db)
        details = analysis_service.get_analysis_details(task_id)
        
        if not details:
            raise HTTPException(status_code=404, detail=f"分析详情不存在: {task_id}")
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析详情失败: {str(e)}")


@router.post("/tasks/{task_id}/mark-violation")
async def mark_task_violation(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    标记任务为违规
    
    - **task_id**: 任务ID
    """
    try:
        # 这里可以调用任务服务来更新状态
        from app.services.task_service import TaskService
        from app.core.constants import TaskStatus
        
        task_service = TaskService(db)
        
        # 检查任务是否存在
        task = task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        # 更新任务状态为确认伪造
        ok = task_service.update_task_status_with_log(task_id, TaskStatus.CONFIRMED_FORGERY)
        if not ok:
            raise HTTPException(status_code=400, detail="状态更新失败")
        
        logger.info(f"任务 {task_id} 已标记为违规")
        
        return {
            "success": True,
            "message": f"任务 {task_id} 已标记为违规",
            "new_status": TaskStatus.CONFIRMED_FORGERY.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记违规失败: {e}")
        raise HTTPException(status_code=500, detail=f"标记违规失败: {str(e)}")


@router.post("/tasks/{task_id}/mark-safe")
async def mark_task_safe(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    标记任务为无风险
    
    - **task_id**: 任务ID
    """
    try:
        from app.services.task_service import TaskService
        from app.core.constants import TaskStatus
        
        task_service = TaskService(db)
        
        # 检查任务是否存在
        task = task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        # 更新任务状态为确认安全
        ok = task_service.update_task_status_with_log(task_id, TaskStatus.CONFIRMED_SAFE)
        if not ok:
            raise HTTPException(status_code=400, detail="状态更新失败")
        
        logger.info(f"任务 {task_id} 已标记为无风险")
        
        return {
            "success": True,
            "message": f"任务 {task_id} 已标记为无风险",
            "new_status": TaskStatus.CONFIRMED_SAFE.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记无风险失败: {e}")
        raise HTTPException(status_code=500, detail=f"标记无风险失败: {str(e)}")
