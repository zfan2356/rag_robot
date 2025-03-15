import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.dao.documents import DocumentDAO
from src.embd import OllamaEmbedding

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentStore:
    """文档存储类，用于管理和检索文档"""

    def __init__(
        self,
        embedding_model: Optional[OllamaEmbedding] = None,
        db_url: str = "mysql+pymysql://root:123456@localhost/rag_robot",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """初始化文档存储

        Args:
            embedding_model: 嵌入模型，用于向量化文档
            db_url: 数据库连接URL
            chunk_size: 文档分块大小
            chunk_overlap: 文档分块重叠大小
        """
        # 初始化嵌入模型
        self.embedding_model = embedding_model or OllamaEmbedding(
            model_name="nomic-embed-text:latest", normalize_vectors=True
        )

        # 初始化文档DAO
        self.doc_dao = DocumentDAO(db_url=db_url)

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

        logger.info(f"DocumentStore初始化完成，使用数据库: {db_url}")

    def add_document(self, content: str, title: Optional[str] = None) -> int:
        """添加文档到存储

        Args:
            content: 文档内容
            title: 文档标题

        Returns:
            int: 文档ID
        """
        # 保存到数据库
        doc_id = self.doc_dao.create(doc=content, title=title)
        logger.info(f"文档添加成功，ID: {doc_id}, 标题: {title or '无标题'}")
        return doc_id

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """获取文档

        Args:
            doc_id: 文档ID

        Returns:
            Optional[Dict[str, Any]]: 文档信息
        """
        return self.doc_dao.get(doc_id)

    def delete_document(self, doc_id: int) -> bool:
        """删除文档

        Args:
            doc_id: 文档ID

        Returns:
            bool: 是否删除成功
        """
        return self.doc_dao.delete(doc_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        """列出所有文档

        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        return self.doc_dao.list_all()

    def search_documents(self, keyword: str) -> List[Dict[str, Any]]:
        """关键词搜索文档

        Args:
            keyword: 搜索关键词

        Returns:
            List[Dict[str, Any]]: 匹配的文档列表
        """
        return self.doc_dao.search_documents(keyword=keyword)

    def get_document_chunks(self, doc_id: int) -> List[LangchainDocument]:
        """获取文档分块

        Args:
            doc_id: 文档ID

        Returns:
            List[LangchainDocument]: 文档分块列表
        """
        # 获取文档
        doc = self.doc_dao.get(doc_id)
        if not doc:
            logger.warning(f"文档不存在，ID: {doc_id}")
            return []

        # 分割文档
        text_chunks = self.text_splitter.split_text(doc["doc"])

        # 转换为Langchain文档格式
        langchain_docs = []
        for i, chunk in enumerate(text_chunks):
            langchain_docs.append(
                LangchainDocument(
                    page_content=chunk,
                    metadata={
                        "source": f"doc_{doc_id}",
                        "chunk_id": i,
                        "title": doc.get("title", "无标题"),
                        "doc_id": doc_id,
                    },
                )
            )

        logger.info(f"文档 {doc_id} 分割为 {len(langchain_docs)} 个块")
        return langchain_docs

    def get_all_document_chunks(self) -> List[LangchainDocument]:
        """获取所有文档的分块

        Returns:
            List[LangchainDocument]: 所有文档分块列表
        """
        # 获取所有文档ID
        docs = self.doc_dao.list_all()
        doc_ids = [doc["id"] for doc in docs]

        # 获取所有文档分块
        all_chunks = []
        for doc_id in doc_ids:
            chunks = self.get_document_chunks(doc_id)
            all_chunks.extend(chunks)

        logger.info(f"总共获取 {len(all_chunks)} 个文档块")
        return all_chunks
