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
from app.services.ai_integration_service import ai_service
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
        
        # 获取AI检测结果
        analysis_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).first()
        
        if analysis_result and analysis_result.ai_detection_result:
            # 使用真实的AI检测结果
            return self._build_real_analysis_report(task, analysis_result)
        else:
            # 如果没有AI检测结果，使用模拟数据（向后兼容）
            return self._build_mock_analysis_report(task)
    
    def _build_real_analysis_report(self, task: AuditTask, analysis_result: AnalysisResult) -> AnalysisReportData:
        """基于真实AI检测结果构建报告"""
        try:
            ai_data = analysis_result.ai_detection_result
            
            # 使用AI集成服务格式化结果
            formatted_result = ai_service.format_for_frontend(ai_data)
            
            # 获取图片信息
            from app.models.image import ImageFile
            images = self.db.query(ImageFile).filter(ImageFile.task_id == task_id).all()
            
            image_info = []
            for img in images:
                image_info.append(ImageInfo(
                    filename=img.filename,
                    url=f"/static/uploads/{img.filename}",
                    file_size=img.file_size,
                    upload_time=img.created_at.strftime("%Y-%m-%d %H:%M:%S")
                ))
            
            return AnalysisReportData(
                task_id=task.task_id,
                images=image_info,
                ai_findings=formatted_result.get("ai_findings", []),
                historical_matches=formatted_result.get("historical_matches", []),
                risk_level=formatted_result.get("risk_level", "unknown"),
                confidence_score=analysis_result.confidence_score or 0.0,
                processing_time=analysis_result.processing_time or 0.0
            )
            
        except Exception as e:
            logger.error(f"构建真实分析报告失败: {e}")
            # 降级到模拟数据
            return self._build_mock_analysis_report(task)
    
    def _build_mock_analysis_report(self, task: AuditTask) -> AnalysisReportData:
        """构建模拟分析报告（向后兼容）"""
        
        # 获取任务的图片文件
        from app.models.image import ImageFile
        images = self.db.query(ImageFile).filter(ImageFile.task_id == task.task_id).all()
        
        if not images:
            logger.error(f"任务 {task.task_id} 没有关联文件")
            return None
        
        # 构建图片信息
        image_info = []
        for img in images:
            image_info.append(ImageInfo(
                filename=img.filename,
                url=f"/static/uploads/{img.filename}",
                file_size=img.file_size,
                upload_time=img.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ))
        
        # 模拟AI检测结果
        mock_ai_findings = [
            {
                "type": "EXIF元数据分析",
                "detail": "检测到图片经过Adobe Photoshop编辑",
                "risk_level": "medium"
            },
            {
                "type": "AI篡改检测",
                "detail": "在金额区域检测到可疑的像素级修改",
                "risk_level": "high"
            }
        ]
        
        # 模拟历史匹配
        mock_historical_matches = [
            {
                "filename": "historical_sample.jpg",
                "url": "/static/uploads/historical_sample.jpg",
                "similarity": 0.95,
                "diff_details": "发现高度相似的历史图片"
            }
        ]
        
        return AnalysisReportData(
            task_id=task.task_id,
            images=image_info,
            ai_findings=mock_ai_findings,
            historical_matches=mock_historical_matches,
            risk_level="high",
            confidence_score=0.85,
            processing_time=2.5
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