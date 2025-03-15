import json
import logging
from typing import Any, AsyncGenerator, Generator, List, Optional

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseLLM
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import Generation, LLMResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field, model_validator

from src.config import ModelConfig, ModelConfigManager
from src.llm.context import ContextManager
from src.llm.prompt import PromptManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocalBaseLLM(BaseLLM):
    base_url: str = Field(
        default="http://localhost:11434",
        description="The base URL of the LLM",
        examples=["http://localhost:11434"],
    )
    model: ModelConfig = Field(
        default=ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB"),
        description="Default model is deepseek-r1:7b",
        examples=[ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="The temperature of the model",
        json_schema_extra={"examples": 0.7},
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="The top probability of the probability mass function of the model",
        json_schema_extra={"examples": 0.9},
    )

    @model_validator(mode="after")
    def validate_params(self) -> "LocalBaseLLM":
        """
        pandantic 2
        """
        if not 0 <= self.temperature <= 1:
            raise ValueError("temperature 必须在 0 到 1 之间")
        if not 0 <= self.top_p <= 1:
            raise ValueError("top_p 必须在 0 到 1 之间")
        return self

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """生成方法改造 (返回 LLMResult 而不是 ChatResult)"""
        generations = []
        for prompt in prompts:
            stream = self._stream_response(prompt, **kwargs)
            full_response = "".join([chunk for chunk in stream])
            generations.append([Generation(text=full_response)])
        return LLMResult(generations=generations)

    def stream(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> Generator[str, None, None]:
        """更新 stream 方法以支持 chain"""
        yield from self._stream_response(input, **kwargs)

    async def astream(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """实现异步 stream 方法"""
        for chunk in self.stream(input, config, **kwargs):
            yield chunk

    def _build_request_params(
        self, prompt: str, is_stream: bool = False, **kwargs
    ) -> dict:
        """构建请求参数"""
        return {
            "model": self.model.name,
            "prompt": prompt,
            "stream": is_stream,
            "temperature": self.temperature,
            "top_p": self.top_p,
            **kwargs,
        }

    def _stream_response(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        params = self._build_request_params(prompt, True, **kwargs)
        resp = self._send_request(params, True)

        for line in resp.iter_lines():
            if line:
                decode_line = line.decode("utf-8")
                yield self._parse_stream_chunk(decode_line)

    def _send_request(
        self,
        params: dict,
        is_stream: bool = False,
    ) -> requests.Response:
        """发送请求并处理响应"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=params,
            timeout=60,
            stream=is_stream,
        )
        response.raise_for_status()
        return response

    def _parse_stream_chunk(self, chunk: str) -> str:
        """解析流式数据块"""
        try:
            return json.loads(chunk).get("response", "")
        except json.decoder.JSONDecodeError:
            return ""

    @property
    def _llm_type(self) -> str:
        return "custom_ollama"

    def invoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> str:
        """实现 invoke 方法以支持 chain 操作"""
        # 生成响应
        result = self._generate([input], **kwargs)
        return result.generations[0][0].text

    async def ainvoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> str:
        """实现异步 invoke 方法"""
        return self.invoke(input, config, **kwargs)


class RagRobotLLM(BaseLLM):
    """基于上下文管理的LLM，继承自BaseLLM以支持LangChain接口"""

    context_manager: ContextManager = Field(
        description="上下文管理器，用于管理对话历史"
    )
    llm: LocalBaseLLM = Field(description="底层LLM实例")

    class Config:
        """配置类"""

        arbitrary_types_allowed = True

    def clear_history(self):
        """清除对话历史记录"""
        self.context_manager.clear_history()

    def _generate(
        self,
        prompt: str,
        context: str = None,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """实现 _generate 方法以支持 BaseLLM 接口"""
        generations = []
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        template = self.context_manager.get_prompt_template()
        formatted_prompt = ""
        # 使用 format 方法将输入格式化为字符串
        if not self.context_manager.is_rag_mode:
            formatted_prompt = template.format(input=prompt)
        else:
            formatted_prompt = template.format(
                context=context,
                input=prompt,
            )

        result = self.llm.invoke(formatted_prompt)

        # 添加用户输入和助手回复到历史记录
        if self.context_manager.is_rag_mode:
            self.context_manager.after_add_user_message(prompt, context)
        else:
            self.context_manager.after_add_user_message(prompt)

        self.context_manager.add_assistant_message(result)

        generations.append([Generation(text=result)])

        return LLMResult(generations=generations)

    def invoke(
        self, input: Any, config: Optional[RunnableConfig] = None, **kwargs
    ) -> str:
        """实现 invoke 方法以支持 chain 操作和链式传递"""
        # 处理不同类型的输入
        if hasattr(input, "messages"):
            # 处理 ChatPromptValue 类型的输入
            messages = input.messages
            # 提取最后一条人类消息作为输入
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    prompt = msg.content
                    break
            else:
                prompt = messages[-1].content if messages else ""
        elif isinstance(input, str):
            prompt = input
        elif isinstance(input, dict):
            # 处理字典类型输入，特别是从 _format_context 传递过来的
            # 优先使用 input 字段，如果没有则尝试使用 question 字段
            prompt = input.get("input", input.get("question", ""))

            # 如果有上下文信息，将其添加到提示中
            context = input.get("context", "")
        else:
            raise ValueError(f"不支持的输入类型: {type(input)}")

        # 生成响应
        result = None
        if not self.context_manager.is_rag_mode:
            result = self._generate(prompt, **kwargs)
        else:
            result = self._generate(prompt, context, **kwargs)
        return result.generations[0][0].text

    def stream(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> Generator[str, None, None]:
        """实现流式生成方法"""
        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        template = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = template.format(input=input)

        response_chunks = []
        # 调用底层LLM的流式生成方法
        for chunk in self.llm.stream(formatted_prompt, **kwargs):
            response_chunks.append(chunk)
            yield chunk

        # 添加用户输入和完整的助手回复到历史记录
        self.context_manager.after_add_user_message(input)
        self.context_manager.add_assistant_message("".join(response_chunks))

    async def ainvoke(
        self, input: Any, config: Optional[RunnableConfig] = None, **kwargs
    ) -> str:
        """实现异步 invoke 方法"""
        # 处理不同类型的输入
        if hasattr(input, "messages"):
            # 处理 ChatPromptValue 类型的输入
            messages = input.messages
            # 提取最后一条人类消息作为输入
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    prompt = msg.content
                    break
            else:
                prompt = messages[-1].content if messages else ""
        elif isinstance(input, (list, tuple)) and all(
            isinstance(m, BaseMessage) for m in input
        ):
            # 处理消息列表
            # 提取最后一条人类消息作为输入
            for msg in reversed(input):
                if isinstance(msg, HumanMessage):
                    prompt = msg.content
                    break
            else:
                prompt = input[-1].content if input else ""
        elif isinstance(input, str):
            prompt = input
        elif isinstance(input, dict):
            # 处理字典类型输入，特别是从 _format_context 传递过来的
            # 优先使用 input 字段，如果没有则尝试使用 question 字段
            prompt = input.get("input", input.get("question", ""))

            # 如果有上下文信息，将其添加到提示中
            context = input.get("context", "")
            if context:
                # 如果是 RAG 模式，上下文已经由 ContextManager 处理
                # 这里只需要确保 prompt 包含用户的问题
                if (
                    not hasattr(self.context_manager, "is_rag_mode")
                    or not self.context_manager.is_rag_mode
                ):
                    prompt = f"上下文信息:\n{context}\n\n问题: {prompt}"
        else:
            raise ValueError(f"不支持的输入类型: {type(input)}")

        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        template = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = template.format(input=prompt)

        # 调用底层LLM
        response = await self.llm.ainvoke(formatted_prompt, **kwargs)

        # 添加用户输入和助手回复到历史记录
        self.context_manager.after_add_user_message(prompt)
        self.context_manager.add_assistant_message(response)

        return response

    async def astream(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """实现异步流式生成方法"""
        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        template = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = template.format(input=input)

        response_chunks = []
        # 调用底层LLM的异步流式生成方法
        async for chunk in self.llm.astream(formatted_prompt, **kwargs):
            response_chunks.append(chunk)
            yield chunk

        # 添加用户输入和完整的助手回复到历史记录
        self.context_manager.after_add_user_message(input)
        self.context_manager.add_assistant_message("".join(response_chunks))

    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return "rag_robot_llm"

    # 保留原有方法作为别名，以保持向后兼容性
    def generate(self, input: str) -> str:
        """生成响应（兼容旧接口）"""
        return self.invoke(input)

    def stream_generate(self, input: str) -> Generator[str, None, None]:
        """流式生成响应（兼容旧接口）"""
        yield from self.stream(input)

    async def agenerate(self, input: str) -> str:
        """异步生成响应（兼容旧接口）"""
        return await self.ainvoke(input)

    async def astream_generate(self, input: str) -> AsyncGenerator[str, None]:
        """异步流式生成响应（兼容旧接口）"""
        async for chunk in self.astream(input):
            yield chunk
