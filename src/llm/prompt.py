from typing import Any, Dict, List, Optional

from src.dao.prompt import PromptDAO


class PromptManager:
    def __init__(self, db_url: str = "mysql+pymysql://root:123456@localhost/rag_robot"):
        """初始化 PromptManager"""
        self.dao = PromptDAO(db_url)

    def create_template(
        self,
        system_prompt: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[int]:
        """创建新的提示词模板

        Args:
            system_prompt: 系统提示词
            name: 模板名称
            description: 模板描述

        Returns:
            Optional[int]: 新创建的模板ID
        """
        return self.dao.create(
            system_prompt=system_prompt, name=name, description=description
        )

    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """获取提示词模板

        Args:
            template_id: 模板ID

        Returns:
            Optional[Dict[str, Any]]: 模板信息，不存在则返回None
        """
        return self.dao.get(template_id)

    def update_template(
        self,
        template_id: int,
        system_prompt: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """更新提示词模板

        Args:
            template_id: 模板ID
            system_prompt: 系统提示词
            name: 模板名称
            description: 模板描述

        Returns:
            bool: 更新是否成功
        """
        return self.dao.update(
            template_id=template_id,
            system_prompt=system_prompt,
            name=name,
            description=description,
        )

    def delete_template(self, template_id: int) -> bool:
        """删除提示词模板

        Args:
            template_id: 模板ID

        Returns:
            bool: 删除是否成功
        """
        return self.dao.delete(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有提示词模板

        Returns:
            List[Dict[str, Any]]: 模板列表
        """
        return self.dao.list_all()

    def get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """通过名称获取模板

        Args:
            name: 模板名称

        Returns:
            Optional[Dict[str, Any]]: 模板信息，不存在则返回None
        """
        return self.dao.get_by_name(name)
