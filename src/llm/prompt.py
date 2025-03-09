from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.dao.prompt import PromptDAO


class PromptManager:
    def __init__(self, db_url: str = "mysql+pymysql://user:password@localhost/db_name"):
        """初始化 PromptManager"""
        self.dao = PromptDAO(db_url)

    def create_template(
        self,
        template_id: str,
        name: str,
        template_content: List[tuple],
        description: str = "",
    ) -> Optional[ChatPromptTemplate]:
        """创建新的提示词模板"""
        if self.dao.create(template_id, name, template_content, description):
            return ChatPromptTemplate(template_content)
        return None

    def get_template(self, template_id: str) -> Optional[ChatPromptTemplate]:
        """获取提示词模板"""
        template_data = self.dao.get(template_id)
        if template_data:
            return ChatPromptTemplate(template_data["template_content"])
        return None

    def update_template(
        self,
        template_id: str,
        template_content: List[tuple],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[ChatPromptTemplate]:
        """更新提示词模板"""
        if self.dao.update(template_id, template_content, name, description):
            return ChatPromptTemplate(template_content)
        return None

    def delete_template(self, template_id: str) -> bool:
        """删除提示词模板"""
        return self.dao.delete(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有提示词模板"""
        return self.dao.list_all()

    def format_history(self, history: List[Dict[str, Any]]) -> List[Any]:
        """格式化对话历史"""
        formatted_messages = []
        for message in history:
            if message["role"] == "user":
                formatted_messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                formatted_messages.append(AIMessage(content=message["content"]))
        return formatted_messages


# 使用示例
if __name__ == "__main__":
    # 初始化管理器
    prompt_manager = PromptManager("mysql+pymysql://user:password@localhost/prompts")

    # 创建默认模板
    default_template = [
        ("system", "你是一个专业的AI助手，擅长回答各类问题。"),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]

    template = prompt_manager.create_template(
        template_id="default",
        name="默认对话模板",
        template_content=default_template,
        description="通用对话模板",
    )

    if template:
        # 使用模板
        messages = template.format_messages(input="你好", chat_history=[])
        print(messages)
