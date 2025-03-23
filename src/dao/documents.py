import json
import logging
import os
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

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Document(Base):
    """文档数据模型"""

    __tablename__ = "document_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doc = Column(Text(length=4294967295), nullable=False)  # LONGTEXT类型
    title = Column(String(255))


class DocumentDAO:
    def __init__(self):
        """初始化数据访问对象"""
        try:
            # 从环境变量获取数据库配置
            db_host = os.getenv("MYSQL_HOST", "localhost")
            db_user = os.getenv("MYSQL_USER", "root")
            db_password = os.getenv("MYSQL_PASSWORD", "123456")
            db_name = os.getenv("MYSQL_DATABASE", "rag_robot")

            db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
            logger.info(f"Connecting to database at {db_host}")
            self.engine = create_engine(db_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Successfully initialized database connection")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise

    def create(
        self,
        doc: str,
        title: Optional[str] = None,
    ) -> int:
        """创建文档记录"""
        session = self.Session()
        try:
            document = Document(
                doc=doc,
                title=title,
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
                session.query(Document).filter(Document.id == document_id).first()
            )

            if not document:
                return None

            return {
                "id": document.id,
                "doc": document.doc,
                "title": document.title,
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
    ) -> bool:
        """更新文档记录"""
        session = self.Session()
        try:
            document = (
                session.query(Document).filter(Document.id == document_id).first()
            )

            if not document:
                return False

            if doc is not None:
                document.doc = doc
            if title is not None:
                document.title = title

            session.commit()
            return True
        finally:
            session.close()

    def delete(self, document_id: int) -> bool:
        """删除文档记录"""
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

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有文档"""
        session = self.Session()
        try:
            documents = session.query(Document).all()

            return [
                {
                    "id": d.id,
                    "title": d.title,
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
    ) -> List[Dict[str, Any]]:
        """搜索文档"""
        session = self.Session()
        try:
            query = session.query(Document)

            if keyword:
                # 在标题和文档内容中搜索关键词
                query = query.filter(
                    (Document.title.like(f"%{keyword}%"))
                    | (Document.doc.like(f"%{keyword}%"))
                )

            documents = query.all()

            return [
                {
                    "id": d.id,
                    "title": d.title,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                    # 不返回完整文档内容，避免数据量过大
                    "doc_preview": d.doc[:200] + "..." if len(d.doc) > 200 else d.doc,
                }
                for d in documents
            ]
        finally:
            session.close()

    def get_document_count(self) -> Dict[str, int]:
        """获取文档统计信息"""
        logger.info("Getting document count")
        session = self.Session()
        try:
            total_count = session.query(Document).count()
            logger.info(f"Document count: {total_count}")
            return {
                "total": total_count,
            }
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            raise
        finally:
            session.close()
