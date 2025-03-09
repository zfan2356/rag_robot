import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class PromptTemplate(Base):
    """提示词模板数据模型"""

    __tablename__ = "prompt_templates"

    template_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    template_content = Column(Text, nullable=False)  # JSON 格式存储模板内容
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptDAO:
    def __init__(self, db_url: str = "mysql+pymysql://user:password@localhost/db_name"):
        """初始化数据访问对象"""
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create(
        self,
        template_id: str,
        name: str,
        template_content: List[tuple],
        description: str = "",
    ) -> bool:
        """创建模板记录"""
        session = self.Session()
        try:
            if session.query(PromptTemplate).filter_by(template_id=template_id).first():
                return False

            db_template = PromptTemplate(
                template_id=template_id,
                name=name,
                description=description,
                template_content=json.dumps(template_content),
            )
            session.add(db_template)
            session.commit()
            return True
        finally:
            session.close()

    def get(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取模板记录"""
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate).filter_by(template_id=template_id).first()
            )
            if not template:
                return None

            return {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "template_content": json.loads(template.template_content),
                "created_at": template.created_at,
                "updated_at": template.updated_at,
            }
        finally:
            session.close()

    def update(
        self,
        template_id: str,
        template_content: List[tuple],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """更新模板记录"""
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate).filter_by(template_id=template_id).first()
            )
            if not template:
                return False

            template.template_content = json.dumps(template_content)
            if name:
                template.name = name
            if description:
                template.description = description

            session.commit()
            return True
        finally:
            session.close()

    def delete(self, template_id: str) -> bool:
        """删除模板记录"""
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate).filter_by(template_id=template_id).first()
            )
            if not template:
                return False

            session.delete(template)
            session.commit()
            return True
        finally:
            session.close()

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有模板"""
        session = self.Session()
        try:
            templates = session.query(PromptTemplate).all()
            return [
                {
                    "template_id": t.template_id,
                    "name": t.name,
                    "description": t.description,
                    "template_content": json.loads(t.template_content),
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in templates
            ]
        finally:
            session.close()
