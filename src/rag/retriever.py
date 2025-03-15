import logging
from typing import Any, Callable, Dict, List, Optional, Union

from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LangchainDocument
from langchain_core.retrievers import BaseRetriever

from src.embd import OllamaEmbedding, cosine_similarity
from src.rag.document_store import DocumentStore

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentRetriever(BaseRetriever):
    """文档检索器，用于检索相关文档"""

    def __init__(
        self,
        document_store: DocumentStore,
        embedding_model: Optional[OllamaEmbedding] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
        similarity_fn: Optional[Callable] = None,
    ):
        """初始化文档检索器

        Args:
            document_store: 文档存储
            embedding_model: 嵌入模型，用于向量化查询
            top_k: 返回的最相似文档数量
            similarity_threshold: 相似度阈值，低于此值的文档将被过滤
            similarity_fn: 自定义相似度计算函数
        """
        super().__init__()
        # 使用属性而不是字段
        self._document_store = document_store
        self._embedding_model = embedding_model or document_store.embedding_model
        self._top_k = top_k
        self._similarity_threshold = similarity_threshold
        self._similarity_fn = similarity_fn or cosine_similarity

        # 缓存所有文档块，避免重复获取
        self._document_chunks = None

        logger.info(
            f"DocumentRetriever初始化完成，top_k={top_k}, threshold={similarity_threshold}"
        )

    @property
    def document_store(self) -> DocumentStore:
        """获取文档存储"""
        return self._document_store

    @property
    def embedding_model(self) -> OllamaEmbedding:
        """获取嵌入模型"""
        return self._embedding_model

    @property
    def top_k(self) -> int:
        """获取返回的最相似文档数量"""
        return self._top_k

    @property
    def similarity_threshold(self) -> float:
        """获取相似度阈值"""
        return self._similarity_threshold

    @property
    def similarity_fn(self) -> Callable:
        """获取相似度计算函数"""
        return self._similarity_fn

    def _get_all_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[LangchainDocument]:
        """检索所有相关文档

        Args:
            query: 查询文本
            run_manager: 回调管理器

        Returns:
            List[LangchainDocument]: 相关文档列表
        """
        # 获取所有文档块（如果尚未缓存）
        if self._document_chunks is None:
            logger.info("首次检索，加载所有文档块")
            self._document_chunks = self.document_store.get_all_document_chunks()

            if not self._document_chunks:
                logger.warning("没有可用的文档块")
                return []

        # 获取查询的嵌入向量
        query_embedding = self.embedding_model.get_embeddings([query])[0]

        # 为所有文档块计算嵌入向量（如果尚未计算）
        if not hasattr(self, "_chunk_embeddings"):
            logger.info("计算所有文档块的嵌入向量")
            chunk_texts = [doc.page_content for doc in self._document_chunks]
            self._chunk_embeddings = self.embedding_model.get_embeddings(chunk_texts)

        # 计算相似度
        similarities = []
        for i, chunk_embedding in enumerate(self._chunk_embeddings):
            similarity = self.similarity_fn(query_embedding, chunk_embedding)
            similarities.append((i, similarity))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 过滤低于阈值的结果并限制数量
        filtered_similarities = [
            (i, sim) for i, sim in similarities if sim >= self.similarity_threshold
        ][: self.top_k]

        # 获取相关文档
        results = []
        for i, similarity in filtered_similarities:
            doc = self._document_chunks[i]
            # 添加相似度到元数据
            doc.metadata["similarity"] = similarity
            results.append(doc)

        logger.info(f"查询 '{query}' 检索到 {len(results)} 个相关文档块")
        return results

    def clear_cache(self):
        """清除缓存的文档块和嵌入向量"""
        self._document_chunks = None
        if hasattr(self, "_chunk_embeddings"):
            delattr(self, "_chunk_embeddings")
        logger.info("检索器缓存已清除")

    def update_cache(self):
        """更新缓存的文档块和嵌入向量"""
        self.clear_cache()
        self._document_chunks = self.document_store.get_all_document_chunks()
        chunk_texts = [doc.page_content for doc in self._document_chunks]
        self._chunk_embeddings = self.embedding_model.get_embeddings(chunk_texts)
        logger.info(f"检索器缓存已更新，共 {len(self._document_chunks)} 个文档块")

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[LangchainDocument]:
        """检索相关文档，可以指定文档ID范围

        Args:
            query: 查询文本
            run_manager: 回调管理器

        Returns:
            List[LangchainDocument]: 相关文档列表
        """
        # 从上下文中获取可能的doc_ids
        doc_ids = None
        if run_manager and hasattr(run_manager, "context") and run_manager.context:
            doc_ids = run_manager.context.get("doc_ids")

        # 如果指定了文档ID，则只在这些文档中检索
        if doc_ids:
            # 获取指定文档的所有块
            chunks = []
            for doc_id in doc_ids:
                chunks.extend(self.document_store.get_document_chunks(doc_id))

            if not chunks:
                logger.warning(f"指定的文档ID {doc_ids} 没有可用的文档块")
                return []

            # 获取查询的嵌入向量
            query_embedding = self.embedding_model.get_embeddings([query])[0]

            # 计算所有块的嵌入向量
            chunk_texts = [doc.page_content for doc in chunks]
            chunk_embeddings = self.embedding_model.get_embeddings(chunk_texts)

            # 计算相似度
            similarities = []
            for i, chunk_embedding in enumerate(chunk_embeddings):
                similarity = self.similarity_fn(query_embedding, chunk_embedding)
                similarities.append((i, similarity))

            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)

            # 过滤低于阈值的结果并限制数量
            filtered_similarities = [
                (i, sim) for i, sim in similarities if sim >= self.similarity_threshold
            ][: self.top_k]

            # 获取相关文档
            results = []
            for i, similarity in filtered_similarities:
                doc = chunks[i]
                # 添加相似度到元数据
                doc.metadata["similarity"] = similarity
                results.append(doc)

            logger.info(
                f"在指定文档中查询 '{query}' 检索到 {len(results)} 个相关文档块"
            )
            return results
        else:
            # 使用内部方法检索所有文档
            return self._get_all_relevant_documents(query, run_manager=run_manager)

    # 保留这个方法用于向后兼容，但将实际工作委托给_get_relevant_documents
    def get_relevant_documents(
        self, query: str, doc_ids: Optional[List[int]] = None
    ) -> List[LangchainDocument]:
        """检索相关文档，可以指定文档ID范围（向后兼容方法）

        Args:
            query: 查询文本
            doc_ids: 文档ID列表，如果提供，则只在这些文档中检索

        Returns:
            List[LangchainDocument]: 相关文档列表
        """
        # 如果指定了文档ID，则只在这些文档中检索
        if doc_ids:
            # 获取指定文档的所有块
            chunks = []
            for doc_id in doc_ids:
                chunks.extend(self.document_store.get_document_chunks(doc_id))

            if not chunks:
                logger.warning(f"指定的文档ID {doc_ids} 没有可用的文档块")
                return []

            # 获取查询的嵌入向量
            query_embedding = self.embedding_model.get_embeddings([query])[0]

            # 计算所有块的嵌入向量
            chunk_texts = [doc.page_content for doc in chunks]
            chunk_embeddings = self.embedding_model.get_embeddings(chunk_texts)

            # 计算相似度
            similarities = []
            for i, chunk_embedding in enumerate(chunk_embeddings):
                similarity = self.similarity_fn(query_embedding, chunk_embedding)
                similarities.append((i, similarity))

            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)

            # 过滤低于阈值的结果并限制数量
            filtered_similarities = [
                (i, sim) for i, sim in similarities if sim >= self.similarity_threshold
            ][: self.top_k]

            # 获取相关文档
            results = []
            for i, similarity in filtered_similarities:
                doc = chunks[i]
                # 添加相似度到元数据
                doc.metadata["similarity"] = similarity
                results.append(doc)

            logger.info(
                f"在指定文档中查询 '{query}' 检索到 {len(results)} 个相关文档块"
            )
            return results
        else:
            # 使用内部方法检索所有文档
            return self._get_all_relevant_documents(query)
