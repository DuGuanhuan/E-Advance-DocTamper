"""
常量定义模块 - 根据PRD要求简化
"""
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举 - 根据PRD要求定义的四个状态"""
    PROCESSING = "processing"           # 图片上传中以及AI模型处理时的状态
    PENDING_REVIEW = "pending_review"   # AI模型处理完成，等待人工审核的状态
    CONFIRMED_FORGERY = "confirmed_forgery"  # 人工标记"确认伪造"之后的状态
    CONFIRMED_SAFE = "confirmed_safe"   # 人工标记"无风险"之后的状态


class ForgeryType(str, Enum):
    """伪造类型枚举"""
    AMOUNT_TAMPERING = "金额篡改"
    PS_MODIFICATION = "PS修改"
    CONTENT_REPLACEMENT = "内容替换"
    SIGNATURE_FORGERY = "签名伪造"
    SEAL_FORGERY = "印章伪造"
    DATE_MODIFICATION = "日期修改"
    OTHER = "其他"


# UI显示映射 - 根据PRD要求
STATUS_DISPLAY_MAP = {
    TaskStatus.PROCESSING: {
        "text": "处理中",
        "color_variable": "var(--processing-color)",
        "css_class": "status-tag-processing"
    },
    TaskStatus.PENDING_REVIEW: {
        "text": "待核对",
        "color_variable": "var(--medium-risk-color)",
        "css_class": "status-tag-pending"
    },
    TaskStatus.CONFIRMED_FORGERY: {
        "text": "疑似伪造",
        "color_variable": "var(--high-risk-color)",
        "css_class": "status-tag-forgery"
    },
    TaskStatus.CONFIRMED_SAFE: {
        "text": "无风险",
        "color_variable": "var(--low-risk-color)",
        "css_class": "status-tag-safe"
    }
}


class TaskStatusTransition:
    """任务状态转换规则 - 根据PRD状态机逻辑"""
    ALLOWED_TRANSITIONS = {
        TaskStatus.PROCESSING: [TaskStatus.PENDING_REVIEW],
        TaskStatus.PENDING_REVIEW: [TaskStatus.CONFIRMED_FORGERY, TaskStatus.CONFIRMED_SAFE],
        TaskStatus.CONFIRMED_FORGERY: [],  # 终态
        TaskStatus.CONFIRMED_SAFE: []      # 终态
    }
    
    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """检查状态转换是否允许"""
        return to_status in cls.ALLOWED_TRANSITIONS.get(from_status, [])
    
    @classmethod
    def get_allowed_transitions(cls, from_status: TaskStatus) -> list[TaskStatus]:
        """获取当前状态允许的转换目标"""
        return cls.ALLOWED_TRANSITIONS.get(from_status, [])


# 文件类型限制
ALLOWED_FILE_TYPES = {
    "image/jpeg",
    "image/png", 
    "image/jpg",
    "application/pdf"
}

# 文件大小限制 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# 分页默认设置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100