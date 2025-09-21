"""
简单的 EXIF 分析适配器

用途：
- 作为你本地 exif_tamper.py 的封装适配层
- 若未接入你自有实现，则使用 Pillow 读取 EXIF 基础信息，并给出简单风险指示

接口：
- ExifAnalyzer.analyze(image_path: str) -> dict

返回示例：
{
  "camera_make": "Apple",
  "camera_model": "iPhone 14",
  "software": "Adobe Photoshop 2023",
  "creation_time": "2024-09-12 10:00:11",
  "gps_info": { ... } | None,
  "risk_indicators": [
    {"type": "software_modification", "description": "检测到Adobe Photoshop编辑痕迹", "risk_level": "high"}
  ]
}
"""
from __future__ import annotations

from typing import Any, Dict, Optional, List
from datetime import datetime
from .exif_tamper import check_exif_tampering_strategy1


class ExifAnalyzer:
    """基于 exif_tamper 策略一的适配器。

    将返回映射为统一结构，供 AI 集成与前端展示使用。
    """

    def analyze(self, image_path: str) -> Dict[str, Any]:
        raw = check_exif_tampering_strategy1(image_path)
        meta: Dict[str, str] = raw.get("metadata", {}) if isinstance(raw, dict) else {}

        def pick(*keys: str) -> Optional[str]:
            for k in keys:
                v = meta.get(k)
                if v:
                    return v
            return None

        # 映射核心字段
        camera_make = pick("make")
        camera_model = pick("model")
        software = pick("software")
        creation_raw = pick("datetimeoriginal", "datetime", "modifydate")
        creation_time: Optional[str] = None
        if isinstance(creation_raw, str):
            # 常见 EXIF 时间格式 "YYYY:MM:DD HH:MM:SS"
            try:
                creation_time = datetime.strptime(creation_raw, "%Y:%m:%d %H:%M:%S").strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except Exception:
                creation_time = creation_raw

        # 风险指示
        risk_indicators: List[Dict[str, str]] = []
        for reason in (raw.get("reasons") or []):
            level = "medium"
            if isinstance(reason, str) and reason.lower().startswith("detected editing software"):
                level = "high"
            risk_indicators.append(
                {
                    "type": "exif_strategy1",
                    "description": reason,
                    "risk_level": level,
                }
            )

        return {
            "camera_make": camera_make,
            "camera_model": camera_model,
            "software": software,
            "creation_time": creation_time,
            "gps_info": None,  # exif_tamper 当前未解析为结构化坐标
            "risk_indicators": risk_indicators,
            "metadata_sample": {  # 可选：回传少量关键信息用于调试
                k: meta.get(k)
                for k in [
                    "make",
                    "model",
                    "software",
                    "datetimeoriginal",
                    "datetime",
                    "modifydate",
                ]
                if meta.get(k)
            },
        }
