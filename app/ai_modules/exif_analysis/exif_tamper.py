from typing import Dict, List

from PIL import Image
from PIL.ExifTags import TAGS

try:
    import piexif  # optional: decode EXIF bytes inside PNG
    _HAS_PIEXIF = True
except Exception:
    piexif = None  # type: ignore
    _HAS_PIEXIF = False


# 已知编辑软件的关键词列表（小写）
EDITING_SOFTWARE_KEYWORDS: List[str] = [
    "photoshop",
    "gimp",
    "lightroom",
    "snapseed",
    "acdsee",
    "corel",
]


def _normalize_exif_value(value) -> str:
    """将字段值规范为可读字符串。对二进制做摘要展示，避免乱码泛滥。"""
    if value is None:
        return ""
    if isinstance(value, bytes):
        # 尝试解码为 UTF-8 文本；若不可读则用长度+hex前缀摘要
        text = value.decode("utf-8", errors="ignore")
        # 简单可读性判据：可打印字符占比
        printable = sum(32 <= ord(ch) <= 126 for ch in text)
        ratio = (printable / max(len(text), 1)) if text else 0.0
        if text and ratio > 0.85:
            return text
        head = value[:32].hex()
        return f"<bytes len={len(value)} head_hex={head}...>"
    return str(value)


def _extract_normalized_metadata_from_image(img: Image.Image) -> (Dict[str, str], str):
    """按格式提取元数据并规范为统一字典（小写键）。返回 (metadata, format)。"""
    fmt = (img.format or "").upper()
    normalized: Dict[str, str] = {}

    # JPEG: 使用 EXIF
    if fmt == "JPEG":
        # 兼容不同 Pillow 版本
        exif_data_raw = None
        if hasattr(img, "getexif"):
            try:
                exif_obj = img.getexif()  # type: ignore[attr-defined]
                exif_data_raw = dict(exif_obj.items()) if exif_obj else None
            except Exception:
                exif_data_raw = None
        if exif_data_raw is None and hasattr(img, "_getexif"):
            try:
                exif_data_raw = img._getexif()  # type: ignore[attr-defined]
            except Exception:
                exif_data_raw = None

        if exif_data_raw:
            for tag_id, value in exif_data_raw.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                key = str(tag_name).lower()
                normalized[key] = _normalize_exif_value(value)

    # PNG: 使用 info 文本块
    elif fmt == "PNG":
        info = getattr(img, "info", None)
        if isinstance(info, dict):
            for k, v in info.items():
                key = str(k).lower()
                normalized[key] = _normalize_exif_value(v)

            # 若存在原始 EXIF 二进制且可用 piexif，尝试解码为键值并合并
            raw_exif = info.get("exif")
            if _HAS_PIEXIF and isinstance(raw_exif, (bytes, bytearray)):
                try:
                    exif_dict = piexif.load(raw_exif)  # type: ignore[attr-defined]
                    for ifd_name, ifd_content in exif_dict.items():
                        if not isinstance(ifd_content, dict):
                            continue
                        for tag_id, val in ifd_content.items():
                            ifd_tags = piexif.TAGS.get(ifd_name, {})  # type: ignore[attr-defined]
                            tag_info = ifd_tags.get(tag_id, {})
                            tag_name = tag_info.get("name", str(tag_id)).lower()
                            key = f"exif.{ifd_name.lower()}.{tag_name}"
                            normalized[key] = _normalize_exif_value(val)
                except Exception:
                    # 解码失败忽略，不影响其他键
                    pass

    else:
        # 其他格式：尽量使用通用路径（有些格式同样在 info 中携带元数据）
        info = getattr(img, "info", None)
        if isinstance(info, dict):
            for k, v in info.items():
                key = str(k).lower()
                normalized[key] = _normalize_exif_value(v)

    return normalized, fmt


def _analyze_normalized_metadata(metadata: Dict[str, str], fmt: str) -> List[str]:
    """基于统一元数据字典进行策略一检测。"""
    reasons: List[str] = []
    if not metadata:
        return reasons

    # 逻辑一：编辑软件标签
    software_val = metadata.get("software")
    if software_val:
        if any(keyword in software_val.lower() for keyword in EDITING_SOFTWARE_KEYWORDS):
            reasons.append(f"Detected editing software: {software_val}")

    # 逻辑二：时间戳不一致（主要针对 JPEG 的 EXIF）
    if fmt == "JPEG":
        dto = metadata.get("datetimeoriginal")
        dt = metadata.get("datetime") or metadata.get("modifydate")
        if dto and dt and dto != dt:
            reasons.append("Timestamp mismatch: ModificationDate is later than OriginalDate.")

    return reasons


def check_exif_tampering_strategy1(image_path: str) -> Dict[str, object]:
    """
    通过分析EXIF元数据检测图片篡改迹象（策略一：软件和时间戳）。

    :param image_path: 图片文件的路径
    :return: 包含检测结果的字典
    """
    result: Dict[str, object] = {
        "is_tampered": False,
        "reasons": [],  # type: List[str]
        "metadata": {},
        "format": "",
    }

    try:
        # 1. 加载图片并提取EXIF数据
        with Image.open(image_path) as img:
            metadata, fmt = _extract_normalized_metadata_from_image(img)

        result["metadata"] = metadata
        result["format"] = fmt
        result["reasons"] = _analyze_normalized_metadata(metadata, fmt)

    except Exception as e:
        # 处理可能发生的错误，如文件不存在或非图片格式
        result["reasons"].append(f"An error occurred: {e}")
        # 返回时由下方逻辑设置 is_tampered
        return result

    # 4. 汇总is_tampered状态
    if result["reasons"]:
        result["is_tampered"] = True

    return result


def check_exif_tampering_strategy1_from_fileobj(file_obj) -> Dict[str, object]:
    """从文件对象（上传流等）进行检测。"""
    result: Dict[str, object] = {"is_tampered": False, "reasons": [], "metadata": {}, "format": ""}
    try:
        with Image.open(file_obj) as img:
            metadata, fmt = _extract_normalized_metadata_from_image(img)
        result["metadata"] = metadata
        result["format"] = fmt
        result["reasons"] = _analyze_normalized_metadata(metadata, fmt)
    except Exception as e:
        result["reasons"].append(f"An error occurred: {e}")
        return result

    if result["reasons"]:
        result["is_tampered"] = True
    return result


__all__ = [
    "check_exif_tampering_strategy1",
    "check_exif_tampering_strategy1_from_fileobj",
    "EDITING_SOFTWARE_KEYWORDS",
]

