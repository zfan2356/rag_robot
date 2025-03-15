from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.llm.prompt import PromptManager
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(
        self,
        prompt_manager: PromptManager,
        template_id: int,
        max_history_length: int = 10,
        is_rag_mode: bool = False,
    ):
        """初始化 ContextManager

        Args:
            prompt_manager: 提示词管理器
            template_id: 提示词模板ID
            max_history_length: 最大历史记录长度，默认为10轮对话
        """
        self.prompt_manager = prompt_manager
        self.template_id = template_id
        self.max_history_length = (
            max_history_length * 2  # 每轮对话包含用户和助手两条消息
        )
        self.history: List[HumanMessage | AIMessage] = []
        self.is_rag_mode = is_rag_mode

        # 获取基础模板
        template = self.prompt_manager.get_template(template_id)
        if not template:
            raise ValueError(f"Template ID {template_id} not found")
        self.system_prompt = template["system_prompt"]

    def clear_history(self):
        """清除对话历史记录"""
        self.history = []

    def pre_add_user_message(self):
        """预处理 - 添加带{input}占位符的消息"""
        if self.is_rag_mode:
            self.history.append(HumanMessage(content="以下是一些参考文档信息:\n{context}"))

        self.history.append(HumanMessage(content="请回答我的问题：{input}"))
        self._trim_history()

    def change_template(self, template_id: int):
        """更换提示词模板"""
        self.template_id = template_id
        self.system_prompt = self.prompt_manager.get_template(template_id)[
            "system_prompt"
        ]
        self.clear_history()

    def after_add_user_message(self, message: str, context: str = None):
        """后处理 - 更新最后一条HumanMessage的内容

        Args:
            message: 用户消息内容
        """
        if not self.is_rag_mode:
            for msg in reversed(self.history):
                if isinstance(msg, HumanMessage) and msg.content.endswith("{input}"):
                    msg.content = msg.content.replace("{input}", message)
                    break
        else:
            cnt = 0
            for msg in reversed(self.history):
                if isinstance(msg, HumanMessage) and msg.content.endswith("{context}"):
                    msg.content = msg.content.replace("{context}", context)
                    cnt += 1
                if isinstance(msg, HumanMessage) and msg.content.endswith("{input}"):
                    msg.content = msg.content.replace("{input}", message)
                    cnt += 1
                    
                if cnt == 2:
                    break

    def add_assistant_message(self, message: str):
        """添加助手消息到历史记录

        Args:
            message: 助手消息内容
        """
        logger.info(f"add_assistant_message: message: {message}")
        self.history.append(AIMessage(content=message))
        self._trim_history()

    def _trim_history(self):
        """保持历史记录在最大长度以内"""
        while len(self.history) > self.max_history_length:
            self.history.pop(0)

    def get_prompt_template(self) -> ChatPromptTemplate:
        """获取包含当前上下文的提示词模板

        Returns:
            ChatPromptTemplate: 包含系统提示词和历史记录的提示词模板
        """
        messages = [("system", self.system_prompt)]
        for msg in self.history:
            role = "human" if isinstance(msg, HumanMessage) else "ai"
            messages.append((role, msg.content))

        return ChatPromptTemplate.from_messages(messages)
