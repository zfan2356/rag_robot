import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Document(Base):
    """文档数据模型"""

    __tablename__ = "document_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # 软删除标记
    doc = Column(Text(length=4294967295), nullable=False)  # LONGTEXT类型
    title = Column(String(255))
    source = Column(String(255))
    doc_type = Column(String(50))
    is_processed = Column(Boolean, default=False)
    metadata = Column(JSON)


class DocumentDAO:
    def __init__(self, db_url: str = "mysql+pymysql://root:123456@localhost/rag_robot"):
        """初始化数据访问对象"""
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create(
        self,
        user: str,
        doc: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        is_processed: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """创建文档记录"""
        session = self.Session()
        try:
            document = Document(
                user=user,
                doc=doc,
                title=title,
                source=source,
                doc_type=doc_type,
                is_processed=is_processed,
                metadata=metadata,
            )
            session.add(document)
            session.commit()
            return document.id  # 返回新创建的ID
        finally:
            session.close()

    def get(self, document_id: int) -> Optional[Dict[str, Any]]:
        """获取文档记录"""
        session = self.Session()
        try:
            document = (
                session.query(Document)
                .filter(
                    Document.id == document_id,
                    Document.deleted_at == None,  # 未删除的记录
                )
                .first()
            )

            if not document:
                return None

            return {
                "id": document.id,
                "user": document.user,
                "doc": document.doc,
                "title": document.title,
                "source": document.source,
                "doc_type": document.doc_type,
                "is_processed": document.is_processed,
                "metadata": document.metadata,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
            }
        finally:
            session.close()

    def update(
        self,
        document_id: int,
        doc: Optional[str] = None,
        title: Optional[str] = None,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        is_processed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """更新文档记录"""
        session = self.Session()
        try:
            document = (
                session.query(Document)
                .filter(
                    Document.id == document_id,
                    Document.deleted_at == None,  # 未删除的记录
                )
                .first()
            )

            if not document:
                return False

            if doc is not None:
                document.doc = doc
            if title is not None:
                document.title = title
            if source is not None:
                document.source = source
            if doc_type is not None:
                document.doc_type = doc_type
            if is_processed is not None:
                document.is_processed = is_processed
            if metadata is not None:
                # 如果已有元数据，则合并，否则直接设置
                if document.metadata:
                    current_metadata = document.metadata.copy()
                    current_metadata.update(metadata)
                    document.metadata = current_metadata
                else:
                    document.metadata = metadata

            session.commit()
            return True
        finally:
            session.close()

    def delete(self, document_id: int) -> bool:
        """软删除文档记录"""
        session = self.Session()
        try:
            document = (
                session.query(Document)
                .filter(
                    Document.id == document_id,
                    Document.deleted_at == None,  # 未删除的记录
                )
                .first()
            )

            if not document:
                return False

            # 软删除：设置删除时间
            document.deleted_at = datetime.utcnow()

            session.commit()
            return True
        finally:
            session.close()

    def hard_delete(self, document_id: int) -> bool:
        """硬删除文档记录（真实删除）"""
        session = self.Session()
        try:
            document = (
                session.query(Document).filter(Document.id == document_id).first()
            )

            if not document:
                return False

            session.delete(document)
            session.commit()
            return True
        finally:
            session.close()

    def list_all(self, processed_only: Optional[bool] = None) -> List[Dict[str, Any]]:
        """列出所有文档"""
        session = self.Session()
        try:
            query = session.query(Document).filter(
                Document.deleted_at == None  # 未删除的记录
            )

            if processed_only is not None:
                query = query.filter(Document.is_processed == processed_only)

            documents = query.all()

            return [
                {
                    "id": d.id,
                    "user": d.user,
                    "title": d.title,
                    "source": d.source,
                    "doc_type": d.doc_type,
                    "is_processed": d.is_processed,
                    "metadata": d.metadata,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                    # 不返回完整文档内容，避免数据量过大
                    "doc_preview": d.doc[:200] + "..." if len(d.doc) > 200 else d.doc,
                }
                for d in documents
            ]
        finally:
            session.close()

    def get_by_user(self, user: str) -> List[Dict[str, Any]]:
        """获取用户上传的所有文档"""
        session = self.Session()
        try:
            documents = (
                session.query(Document)
                .filter(
                    Document.user == user, Document.deleted_at == None  # 未删除的记录
                )
                .all()
            )

            return [
                {
                    "id": d.id,
                    "title": d.title,
                    "source": d.source,
                    "doc_type": d.doc_type,
                    "is_processed": d.is_processed,
                    "metadata": d.metadata,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                    # 不返回完整文档内容，避免数据量过大
                    "doc_preview": d.doc[:200] + "..." if len(d.doc) > 200 else d.doc,
                }
                for d in documents
            ]
        finally:
            session.close()

    def search_documents(
        self,
        keyword: Optional[str] = None,
        doc_type: Optional[str] = None,
        source: Optional[str] = None,
        user: Optional[str] = None,
        is_processed: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """搜索文档"""
        session = self.Session()
        try:
            query = session.query(Document).filter(
                Document.deleted_at == None  # 未删除的记录
            )

            if keyword:
                # 在标题和文档内容中搜索关键词
                query = query.filter(
                    (Document.title.like(f"%{keyword}%"))
                    | (Document.doc.like(f"%{keyword}%"))
                )

            if doc_type:
                query = query.filter(Document.doc_type == doc_type)

            if source:
                query = query.filter(Document.source == source)

            if user:
                query = query.filter(Document.user == user)

            if is_processed is not None:
                query = query.filter(Document.is_processed == is_processed)

            documents = query.all()

            return [
                {
                    "id": d.id,
                    "user": d.user,
                    "title": d.title,
                    "source": d.source,
                    "doc_type": d.doc_type,
                    "is_processed": d.is_processed,
                    "metadata": d.metadata,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                    # 不返回完整文档内容，避免数据量过大
                    "doc_preview": d.doc[:200] + "..." if len(d.doc) > 200 else d.doc,
                }
                for d in documents
            ]
        finally:
            session.close()

    def mark_as_processed(self, document_id: int) -> bool:
        """标记文档为已处理"""
        return self.update(document_id, is_processed=True)

    def get_document_count(self) -> Dict[str, int]:
        """获取文档统计信息"""
        session = self.Session()
        try:
            total_count = (
                session.query(Document).filter(Document.deleted_at == None).count()
            )

            processed_count = (
                session.query(Document)
                .filter(Document.deleted_at == None, Document.is_processed == True)
                .count()
            )

            unprocessed_count = (
                session.query(Document)
                .filter(Document.deleted_at == None, Document.is_processed == False)
                .count()
            )

            return {
                "total": total_count,
                "processed": processed_count,
                "unprocessed": unprocessed_count,
            }
        finally:
            session.close()
