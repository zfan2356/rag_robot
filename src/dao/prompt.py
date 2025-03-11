import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class PromptTemplate(Base):
    """提示词模板数据模型"""

    __tablename__ = "prompt_template_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    system_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    name = Column(String(100))  # 模板名称
    description = Column(String(500))  # 模板描述


class PromptDAO:
    def __init__(
        self,
        db_url: str = "mysql+pymysql://root:123456@localhost/rag_robot?charset=utf8mb4",
    ):
        """初始化数据访问对象"""
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create(
        self,
        system_prompt: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> int:
        """创建模板记录

        Args:
            system_prompt: 系统提示词
            name: 模板名称
            description: 模板描述

        Returns:
            int: 新创建的模板ID
        """
        session = self.Session()
        try:
            prompt_template = PromptTemplate(
                system_prompt=system_prompt,
                name=name,
                description=description,
            )
            session.add(prompt_template)
            session.commit()
            return prompt_template.id
        finally:
            session.close()

    def get(self, template_id: int) -> Optional[Dict[str, Any]]:
        """获取模板记录

        Args:
            template_id: 模板ID

        Returns:
            Optional[Dict[str, Any]]: 模板信息，不存在则返回None
        """
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate)
                .filter(PromptTemplate.id == template_id)
                .first()
            )

            if not template:
                return None

            return {
                "id": template.id,
                "system_prompt": template.system_prompt,
                "name": template.name,
                "description": template.description,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
            }
        finally:
            session.close()

    def update(
        self,
        template_id: int,
        system_prompt: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """更新模板记录

        Args:
            template_id: 模板ID
            system_prompt: 系统提示词
            name: 模板名称
            description: 模板描述

        Returns:
            bool: 更新是否成功
        """
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate)
                .filter(PromptTemplate.id == template_id)
                .first()
            )

            if not template:
                return False

            if system_prompt is not None:
                template.system_prompt = system_prompt
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description

            session.commit()
            return True
        finally:
            session.close()

    def delete(self, template_id: int) -> bool:
        """删除模板记录

        Args:
            template_id: 模板ID

        Returns:
            bool: 删除是否成功
        """
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate)
                .filter(PromptTemplate.id == template_id)
                .first()
            )

            if not template:
                return False

            session.delete(template)
            session.commit()
            return True
        finally:
            session.close()

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有模板

        Returns:
            List[Dict[str, Any]]: 模板列表
        """
        session = self.Session()
        try:
            templates = session.query(PromptTemplate).all()

            return [
                {
                    "id": t.id,
                    "system_prompt": t.system_prompt,
                    "name": t.name,
                    "description": t.description,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in templates
            ]
        finally:
            session.close()

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """通过名称获取模板

        Args:
            name: 模板名称

        Returns:
            Optional[Dict[str, Any]]: 模板信息，不存在则返回None
        """
        session = self.Session()
        try:
            template = (
                session.query(PromptTemplate)
                .filter(PromptTemplate.name == name)
                .first()
            )

            if not template:
                return None

            return {
                "id": template.id,
                "system_prompt": template.system_prompt,
                "name": template.name,
                "description": template.description,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
            }
        finally:
            session.close()
