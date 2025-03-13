import json
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
        self, input: Any, config: Optional[RunnableConfig] = None, **kwargs
    ) -> str:
        """实现 invoke 方法以支持 chain 操作"""
        # 处理 ChatPromptValue 类型的输入
        if hasattr(input, "messages"):
            # 将所有消息内容合并成一个字符串
            prompt = "\n".join(msg.content for msg in input.messages)
        elif isinstance(input, (list, tuple)) and all(
            isinstance(m, BaseMessage) for m in input
        ):
            # 处理消息列表
            prompt = "\n".join(msg.content for msg in input)
        elif isinstance(input, str):
            prompt = input
        else:
            raise ValueError(f"Unsupported input type: {type(input)}")

        print(f"prompt: {prompt}")
        result = self._generate([prompt], **kwargs)
        return result.generations[0][0].text

    async def ainvoke(
        self, input: Any, config: Optional[RunnableConfig] = None, **kwargs
    ) -> str:
        """实现异步 invoke 方法"""
        return self.invoke(input, config, **kwargs)


class RagRobotLLM:
    def __init__(
        self,
        context_manager: ContextManager,
        llm: LocalBaseLLM,
    ):
        """初始化 RagRobotLLM

        Args:
            context_manager: 上下文管理器
            llm: 本地LLM实例
        """
        self.context_manager = context_manager
        self.llm = llm

    def clear_history(self):
        """清除对话历史记录"""
        self.context_manager.clear_history()

    def generate(self, input: str) -> str:
        """生成响应

        Args:
            input: 用户输入

        Returns:
            str: LLM响应结果
        """
        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板并调用LLM
        prompt = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = prompt.format(input=input)
        result = self.llm.invoke(formatted_prompt)

        # 添加助手回复到历史记录
        self.context_manager.after_add_user_message(input)
        self.context_manager.add_assistant_message(result)

        return result

    def stream_generate(self, input: str) -> Generator[str, None, None]:
        """流式生成响应

        Args:
            input: 用户输入

        Returns:
            Generator[str, None, None]: 生成器，用于流式返回响应
        """
        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        prompt = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = prompt.format(input=input)

        response_chunks = []
        # 调用LLM的流式生成方法
        for chunk in self.llm.stream(formatted_prompt):
            response_chunks.append(chunk)
            yield chunk

        self.context_manager.after_add_user_message(input)
        # 添加完整的助手回复到历史记录
        self.context_manager.add_assistant_message("".join(response_chunks))

    async def agenerate(self, input: str) -> str:
        """异步生成响应

        Args:
            input: 用户输入

        Returns:
            str: LLM响应结果
        """
        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        prompt = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = prompt.format(input=input)

        response = await self.llm.ainvoke(formatted_prompt)

        # 添加助手回复到历史记录
        self.context_manager.after_add_user_message(input)
        self.context_manager.add_assistant_message(response)

        return response

    async def astream_generate(self, input: str) -> AsyncGenerator[str, None]:
        """异步流式生成响应

        Args:
            input: 用户输入

        Returns:
            AsyncGenerator[str, None]: 异步生成器，用于流式返回响应
        """
        # 添加用户输入到历史记录
        self.context_manager.pre_add_user_message()

        # 获取包含历史记录的提示词模板
        prompt = self.context_manager.get_prompt_template()
        # 使用 format 方法将输入格式化为字符串
        formatted_prompt = prompt.format(input=input)

        response_chunks = []
        # 调用LLM的异步流式生成方法
        async for chunk in self.llm.astream(formatted_prompt):
            response_chunks.append(chunk)
            yield chunk

        # 添加完整的助手回复到历史记录
        self.context_manager.after_add_user_message(input)
        self.context_manager.add_assistant_message("".join(response_chunks))
