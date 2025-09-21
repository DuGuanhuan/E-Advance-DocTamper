"""
AI检测集成服务
用于集成EXIF分析、相似图检测、篡改检测等AI能力
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

# 导入你的AI模块（将你的代码移入后取消注释）
from app.ai_modules.exif_analysis.analyzer import ExifAnalyzer
# from app.ai_modules.similarity import SimilarityDetector  
# from app.ai_modules.tampering import TamperingDetector


class AIIntegrationService:
    """AI检测集成服务类"""
    
    def __init__(self):
        """初始化AI检测服务"""
        self.exif_analyzer = ExifAnalyzer()
        self.similarity_detector = None  # SimilarityDetector()
        self.tampering_detector = None  # TamperingDetector()
        
        logger.info("AI集成服务初始化完成")
    
    async def analyze_image_complete(self, image_path: str, task_id: str) -> Dict[str, Any]:
        """
        完整的图像分析流程
        
        Args:
            image_path: 图像文件路径
            task_id: 任务ID
            
        Returns:
            包含所有AI检测结果的字典
        """
        start_time = time.time()
        logger.info(f"开始AI检测分析: {image_path} (任务: {task_id})")
        
        try:
            # 并行执行三种检测
            results = await asyncio.gather(
                self.analyze_exif(image_path),
                self.detect_similarity(image_path),
                self.detect_tampering(image_path),
                return_exceptions=True
            )
            
            exif_result, similarity_result, tampering_result = results
            
            # 处理异常结果
            if isinstance(exif_result, Exception):
                logger.error(f"EXIF分析失败: {exif_result}")
                exif_result = {"error": str(exif_result)}
            
            if isinstance(similarity_result, Exception):
                logger.error(f"相似图检测失败: {similarity_result}")
                similarity_result = {"error": str(similarity_result)}
                
            if isinstance(tampering_result, Exception):
                logger.error(f"篡改检测失败: {tampering_result}")
                tampering_result = {"error": str(tampering_result)}
            
            # 综合分析结果
            analysis_result = {
                "task_id": task_id,
                "image_path": image_path,
                "timestamp": time.time(),
                "processing_time": time.time() - start_time,
                "exif_analysis": exif_result,
                "similarity_detection": similarity_result,
                "tampering_detection": tampering_result,
                "overall_risk_score": self._calculate_risk_score(
                    exif_result, similarity_result, tampering_result
                )
            }
            
            logger.info(f"AI检测完成，耗时: {analysis_result['processing_time']:.2f}秒")
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI检测过程中发生错误: {e}")
            raise
    
    async def analyze_exif(self, image_path: str) -> Dict[str, Any]:
        """EXIF分析：调用真实适配器（同步实现）"""
        logger.info(f"开始EXIF分析: {image_path}")
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self.exif_analyzer.analyze, image_path)
            logger.info("EXIF分析完成")
            return result
        except Exception as e:
            logger.error(f"EXIF分析失败: {e}")
            raise
    
    async def detect_similarity(self, image_path: str) -> Dict[str, Any]:
        """
        相似图检测
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            相似图检测结果
        """
        logger.info(f"开始相似图检测: {image_path}")
        
        try:
            # TODO: 替换为你的相似图检测代码
            # result = self.similarity_detector.detect(image_path)
            
            # 临时模拟结果（替换为真实调用）
            await asyncio.sleep(1.0)  # 模拟处理时间
            result = {
                "total_matches": 2,
                "matches": [
                    {
                        "image_id": "hist_001",
                        "image_path": "/static/uploads/historical_sample.jpg",
                        "similarity_score": 0.95,
                        "match_regions": [
                            {"x": 100, "y": 150, "width": 200, "height": 100}
                        ],
                        "description": "发现高度相似的历史图片"
                    },
                    {
                        "image_id": "hist_002", 
                        "image_path": "/static/uploads/historical_sample2.jpg",
                        "similarity_score": 0.78,
                        "match_regions": [],
                        "description": "发现中等相似的历史图片"
                    }
                ],
                "risk_assessment": {
                    "risk_level": "high",
                    "reason": "发现多个高相似度匹配图片"
                }
            }
            
            logger.info("相似图检测完成")
            return result
            
        except Exception as e:
            logger.error(f"相似图检测失败: {e}")
            raise
    
    async def detect_tampering(self, image_path: str) -> Dict[str, Any]:
        """
        篡改检测
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            篡改检测结果
        """
        logger.info(f"开始篡改检测: {image_path}")
        
        try:
            # TODO: 替换为你的篡改检测代码
            # result = self.tampering_detector.detect(image_path)
            
            # 临时模拟结果（替换为真实调用）
            await asyncio.sleep(1.5)  # 模拟处理时间
            result = {
                "tampering_detected": True,
                "confidence_score": 0.87,
                "tampering_regions": [
                    {
                        "region_id": 1,
                        "bbox": {"x": 250, "y": 300, "width": 150, "height": 80},
                        "tampering_type": "copy_move",
                        "confidence": 0.92,
                        "description": "检测到复制-移动篡改"
                    },
                    {
                        "region_id": 2,
                        "bbox": {"x": 400, "y": 200, "width": 100, "height": 60},
                        "tampering_type": "splicing",
                        "confidence": 0.78,
                        "description": "检测到拼接篡改"
                    }
                ],
                "technical_details": {
                    "algorithm": "CNN-based detection",
                    "model_version": "v2.1",
                    "processing_time": 1.5
                }
            }
            
            logger.info("篡改检测完成")
            return result
            
        except Exception as e:
            logger.error(f"篡改检测失败: {e}")
            raise
    
    def _calculate_risk_score(self, exif_result: Dict, similarity_result: Dict, tampering_result: Dict) -> float:
        """
        计算综合风险评分
        
        Args:
            exif_result: EXIF分析结果
            similarity_result: 相似图检测结果
            tampering_result: 篡改检测结果
            
        Returns:
            风险评分 (0.0-1.0)
        """
        risk_score = 0.0
        
        # EXIF风险评估 (权重: 0.2)
        if not isinstance(exif_result, dict) or "error" in exif_result:
            exif_risk = 0.0
        else:
            exif_risk = len(exif_result.get("risk_indicators", [])) * 0.3
        
        # 相似图风险评估 (权重: 0.3)
        if not isinstance(similarity_result, dict) or "error" in similarity_result:
            similarity_risk = 0.0
        else:
            max_similarity = max([m.get("similarity_score", 0) for m in similarity_result.get("matches", [])], default=0)
            similarity_risk = max_similarity
        
        # 篡改检测风险评估 (权重: 0.5)
        if not isinstance(tampering_result, dict) or "error" in tampering_result:
            tampering_risk = 0.0
        else:
            tampering_risk = tampering_result.get("confidence_score", 0.0) if tampering_result.get("tampering_detected", False) else 0.0
        
        # 加权计算总风险
        risk_score = (exif_risk * 0.2) + (similarity_risk * 0.3) + (tampering_risk * 0.5)
        
        return min(risk_score, 1.0)  # 确保不超过1.0
    
    def format_for_frontend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化AI检测结果供前端使用
        
        Args:
            analysis_result: AI检测原始结果
            
        Returns:
            格式化后的结果
        """
        try:
            # 转换为前端期望的格式
            formatted_result = {
                "task_id": analysis_result["task_id"],
                "processing_time": analysis_result["processing_time"],
                "overall_risk_score": analysis_result["overall_risk_score"],
                "ai_findings": [],
                "historical_matches": [],
                "risk_level": self._get_risk_level(analysis_result["overall_risk_score"])
            }
            
            # 处理EXIF结果
            exif_data = analysis_result.get("exif_analysis", {})
            if not isinstance(exif_data, dict) or "error" not in exif_data:
                for indicator in exif_data.get("risk_indicators", []):
                    formatted_result["ai_findings"].append({
                        "type": "EXIF元数据分析",
                        "detail": indicator["description"],
                        "risk_level": indicator["risk_level"]
                    })
            
            # 处理相似图结果
            similarity_data = analysis_result.get("similarity_detection", {})
            if not isinstance(similarity_data, dict) or "error" not in similarity_data:
                for match in similarity_data.get("matches", []):
                    if match["similarity_score"] >= 0.8:  # 只显示高相似度的
                        formatted_result["historical_matches"].append({
                            "filename": Path(match["image_path"]).name,
                            "url": match["image_path"],
                            "similarity": match["similarity_score"],
                            "diff_details": match["description"]
                        })
            
            # 处理篡改检测结果
            tampering_data = analysis_result.get("tampering_detection", {})
            if not isinstance(tampering_data, dict) or "error" not in tampering_data:
                if tampering_data.get("tampering_detected", False):
                    for region in tampering_data.get("tampering_regions", []):
                        formatted_result["ai_findings"].append({
                            "type": f"AI篡改检测 - {region['tampering_type']}",
                            "detail": f"{region['description']} (置信度: {region['confidence']:.2%})",
                            "risk_level": "high" if region['confidence'] > 0.8 else "medium"
                        })
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"格式化AI结果失败: {e}")
            return {
                "task_id": analysis_result.get("task_id", "unknown"),
                "error": "结果格式化失败",
                "ai_findings": [],
                "historical_matches": [],
                "risk_level": "unknown"
            }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """根据风险评分获取风险等级"""
        if risk_score >= 0.8:
            return "high"
        elif risk_score >= 0.5:
            return "medium"
        elif risk_score >= 0.2:
            return "low"
        else:
            return "safe"


# 全局AI服务实例
ai_service = AIIntegrationService()
