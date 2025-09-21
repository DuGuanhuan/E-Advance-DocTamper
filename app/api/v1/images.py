"""
相似图索引 API

1) POST /images       -> 添加图片到历史库（物理存储 + 向量索引增量）
2) POST /images/search -> 以图搜图（返回相似度>90%的历史图片）
"""
from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from loguru import logger

from app.core.config import settings
from app.services.similarity_index import similarity_index


router = APIRouter()


def _ensure_dirs() -> None:
    os.makedirs(settings.image_library_dir, exist_ok=True)
    os.makedirs(settings.chroma_db_dir, exist_ok=True)


@router.post("/images", status_code=201)
async def add_image_to_library(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
):
    """将图片永久加入历史库与向量索引（增量）。"""
    try:
        _ensure_dirs()

        # 解析可选元信息
        meta_dict = None
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except Exception:
                raise HTTPException(status_code=400, detail="metadata 不是合法JSON字符串")

        # 生成唯一文件名并保存
        ext = os.path.splitext(file.filename or "")[1] or ".jpg"
        image_id = f"{os.urandom(8).hex()}{ext}"
        stored_path = os.path.abspath(os.path.join(settings.image_library_dir, image_id))

        size = 0
        with open(stored_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 128)
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)

        # 增量加入向量索引
        similarity_index.initialize()  # 幂等
        similarity_index.add_image(stored_path, metadata=meta_dict, image_id=image_id)

        logger.info(f"图片已入库: {stored_path} (size={size} bytes)")
        return {
            "status": "success",
            "message": "Image added to the library successfully.",
            "image_id": image_id,
            "stored_path": stored_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加图片失败: {e}")


@router.post("/images/search")
async def search_similar_images(
    file: UploadFile = File(...),
):
    """以图搜图：返回相似度 > 90% 的历史图片。"""
    try:
        _ensure_dirs()

        # 将查询图片落地到临时文件（在图片库下的临时子目录）
        tmp_dir = os.path.join(settings.image_library_dir, "_query_tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.abspath(os.path.join(tmp_dir, f"q_{os.urandom(6).hex()}{os.path.splitext(file.filename or '')[1] or '.jpg'}"))

        with open(tmp_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 128)
                if not chunk:
                    break
                f.write(chunk)

        # 相似检索
        similarity_index.initialize()  # 幂等
        results = similarity_index.search_similar(tmp_path, k=10)

        # 清理查询临时文件（可选保留以调试）
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        if not results:
            return {"status": "not_found", "similar_images": []}

        # 构建响应
        similar_images = [
            {"image_path": path, "similarity": round(sim, 1)} for path, sim in results
        ]
        return {"status": "found", "similar_images": similar_images}
    except Exception as e:
        logger.error(f"相似检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"相似检索失败: {e}")

