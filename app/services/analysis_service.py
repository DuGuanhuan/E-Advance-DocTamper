"""
分析报告服务
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import random

from app.models.task import AuditTask
from app.models.analysis import AnalysisResult
from app.schemas.analysis import (
    AnalysisReportData, ImageInfo, HistoricalMatch, 
    AnalysisDetailItem, AnalysisDetailsResponse
)
from loguru import logger


class AnalysisService:
    """分析报告服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_analysis_report(self, task_id: str) -> Optional[AnalysisReportData]:
        """获取分析报告数据"""
        # 获取任务信息
        task = self.db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return None
        
        # 获取任务的第一个文件
        if not task.files:
            logger.error(f"任务 {task_id} 没有关联文件")
            return None
        
        current_file = task.files[0]  # 取第一个文件
        
        # 构建当前图片信息
        current_image = ImageInfo(
            url=f"/static/uploads/{current_file.file_path}",
            filename=current_file.filename
        )
        
        # 模拟历史匹配逻辑（实际项目中这里会调用AI模型）
        historical_match = self._simulate_historical_match(task_id)
        
        return AnalysisReportData(
            task_id=task_id,
            detection_timestamp=task.updated_at or task.created_at,
            current_image=current_image,
            historical_match=historical_match
        )
    
    def _simulate_historical_match(self, task_id: str) -> Optional[HistoricalMatch]:
        """模拟历史匹配结果（实际项目中会调用AI服务）"""
        # 模拟逻辑：根据任务ID决定是否有历史匹配
        if task_id in ["TSK-010", "TSK-003"]:  # 某些任务有历史匹配
            # 生成90%以上的相似度
            similarity_score = 0.9 + random.random() * 0.09  # 90%-99%
            
            return HistoricalMatch(
                similarity_score=similarity_score,
                image=ImageInfo(
                    url="/static/uploads/historical_sample.jpg",
                    filename=f"historical_{task_id.split('-')[1]}.jpg"
                )
            )
        
        # 其他任务返回低相似度或无匹配
        return None
    
    def get_analysis_details(self, task_id: str) -> Optional[AnalysisDetailsResponse]:
        """获取分析详情"""
        task = self.db.query(AuditTask).filter(AuditTask.task_id == task_id).first()
        if not task:
            return None
        
        # 模拟分析详情（实际项目中会从分析结果表获取）
        details = self._generate_analysis_details(task_id)
        
        return AnalysisDetailsResponse(
            task_id=task_id,
            details=details
        )
    
    def _generate_analysis_details(self, task_id: str) -> list[AnalysisDetailItem]:
        """生成分析详情（模拟数据）"""
        base_details = [
            AnalysisDetailItem(
                label="任务ID",
                content=task_id,
                is_risk=False
            ),
            AnalysisDetailItem(
                label="检测时间",
                content=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                is_risk=False
            )
        ]
        
        # 根据任务ID生成不同的分析结果
        if task_id == "TSK-010":
            # 高风险任务
            risk_details = [
                AnalysisDetailItem(
                    label="相似度",
                    content="95.8%",
                    is_risk=True
                ),
                AnalysisDetailItem(
                    label="AI篡改痕迹检测",
                    content="在金额区域检测到像素级别涂抹与二次填充痕迹",
                    is_risk=True
                ),
                AnalysisDetailItem(
                    label="文字一致性分析",
                    content="数字金额与大写金额不符，疑似篡改",
                    is_risk=True
                ),
                AnalysisDetailItem(
                    label="元数据分析",
                    content="检测到Adobe Photoshop编辑痕迹",
                    is_risk=True
                )
            ]
            return base_details + risk_details
        
        elif task_id == "TSK-003":
            # 中等风险任务
            risk_details = [
                AnalysisDetailItem(
                    label="相似度",
                    content="92.3%",
                    is_risk=True
                ),
                AnalysisDetailItem(
                    label="AI篡改痕迹检测",
                    content="未检测到明显篡改痕迹",
                    is_risk=False
                ),
                AnalysisDetailItem(
                    label="文字一致性分析",
                    content="文字内容基本一致",
                    is_risk=False
                )
            ]
            return base_details + risk_details
        
        else:
            # 低风险或无风险任务
            safe_details = [
                AnalysisDetailItem(
                    label="AI篡改痕迹检测",
                    content="未检测到篡改痕迹",
                    is_risk=False
                ),
                AnalysisDetailItem(
                    label="历史相似度对比",
                    content="未发现高相似度历史图片",
                    is_risk=False
                ),
                AnalysisDetailItem(
                    label="元数据分析",
                    content="文件元数据正常",
                    is_risk=False
                )
            ]
            return base_details + safe_details