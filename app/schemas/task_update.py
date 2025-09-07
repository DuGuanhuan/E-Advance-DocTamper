"""
任务更新相关的Pydantic模式
"""
from pydantic import BaseModel
from app.models.task import TaskStatus

class TaskStatusUpdate(BaseModel):
    """任务状态更新模型"""
    status: TaskStatus