"""
相似图索引服务

职责：
- 在应用启动时初始化 OpenCLIPEmbeddings 与 Chroma（持久化）
- 提供增量添加图片到索引与相似检索能力
- 复用全局单例，避免每次请求重复加载模型/索引
"""
from __future__ import annotations

import os
import uuid
import threading
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from app.core.config import settings


class SimilarityIndex:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._initialized = False
        self._embeddings = None  # OpenCLIPEmbeddings
        self._vector_store = None  # langchain_chroma.Chroma

    def initialize(self) -> None:
        """幂等初始化：加载 OpenCLIP 与持久化 Chroma。"""
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            try:
                # 延迟导入，避免环境未安装时报错阻断应用加载
                from langchain_experimental.open_clip import OpenCLIPEmbeddings
                from langchain_chroma import Chroma

                logger.info("加载 OpenCLIPEmbeddings 模型 (ViT-B-32/laion2b_s34b_b79k)…")
                self._embeddings = OpenCLIPEmbeddings(
                    model_name="ViT-B-32", checkpoint="laion2b_s34b_b79k"
                )

                logger.info(
                    f"初始化 Chroma 持久化向量库: dir={settings.chroma_db_dir}, collection={settings.chroma_collection_name}"
                )
                # 不做任何删除操作，Chroma 会复用已存在集合
                self._vector_store = Chroma(
                    collection_name=settings.chroma_collection_name,
                    embedding_function=self._embeddings,
                    persist_directory=settings.chroma_db_dir,
                )

                self._initialized = True
                logger.info("相似图索引初始化完成（持久化复用，无清空）。")
            except Exception as e:
                logger.error(f"相似图索引初始化失败: {e}")
                raise

    # ---------- 工具 ----------
    def _ensure_ready(self) -> None:
        if not self._initialized:
            self.initialize()

    def _gen_image_id(self, original_filename: str) -> str:
        ext = os.path.splitext(original_filename)[1].lower() or ".jpg"
        return f"{uuid.uuid4().hex}{ext}"

    # ---------- 对外能力 ----------
    def add_image(self, file_path: str, metadata: Optional[Dict[str, Any]] = None, image_id: Optional[str] = None) -> str:
        """将图片增量加入向量库。metadata 中会合并 source=文件路径。"""
        self._ensure_ready()
        meta = {"source": file_path}
        if metadata:
            meta.update(metadata)

        ids = [image_id] if image_id else None
        try:
            self._vector_store.add_images(uris=[file_path], metadatas=[meta], ids=ids)
            logger.info(f"向量库已加入图片: {file_path}")
            return image_id or os.path.basename(file_path)
        except Exception as e:
            logger.error(f"加入图片到向量库失败: {e}")
            raise

    def search_similar(self, query_image_path: str, k: int = 10) -> List[Tuple[str, float]]:
        """以图搜图，返回 (image_path, similarity百分比) 列表，过滤相似度<=90%的项。"""
        self._ensure_ready()
        try:
            # 生成查询向量
            query_vec = self._embeddings.embed_image([query_image_path])[0]
            # 取一个略大的 k，后续按阈值过滤
            results = self._vector_store.similarity_search_by_vector_with_relevance_scores(
                embedding=query_vec, k=k
            )
            output: List[Tuple[str, float]] = []
            for doc, score in results:
                # 参考公式：similarity = (1 - score) * 100
                similarity = (1 - float(score)) * 100.0
                if float(score) < 0.1:  # >90%
                    # 取我们在入库时写入的 file 路径（source）
                    image_path = doc.metadata.get("source") or doc.page_content or ""
                    if image_path:
                        output.append((image_path, similarity))
            return output
        except Exception as e:
            logger.error(f"相似搜索失败: {e}")
            raise


# 全局单例
similarity_index = SimilarityIndex()

