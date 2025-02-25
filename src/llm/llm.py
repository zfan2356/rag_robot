from typing import Any, List, Optional

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import Generation, LLMResult
from pydantic import BaseModel, Field, model_validator

from src.config import ModelConfig, ModelConfigManager


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
            params = self._build_request_params(prompt, **kwargs)
            response = self._send_request(params)
            generations.append([Generation(text=self._parse_response(response))])
        return LLMResult(generations=generations)

    def _build_request_params(self, prompt: str, **kwargs) -> dict:
        """构建请求参数"""
        return {
            "model": self.model.name,
            "prompt": prompt,
            "stream": False,
            "temperature": self.temperature,
            "top_p": self.top_p,
            **kwargs,
        }

    def _send_request(self, params: dict) -> dict:
        """发送请求并处理响应"""
        response = requests.post(
            f"{self.base_url}/api/generate", json=params, timeout=60
        )
        response.raise_for_status()
        return response.json()

    def _parse_response(self, response: dict) -> str:
        """解析响应数据"""
        return response["response"]

    @property
    def _llm_type(self) -> str:
        return "custom_ollama"


if __name__ == "__main__":
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")
    llm = LocalBaseLLM(model=model_config)

    for i in range(1, 4):
        # 获取用户输入
        user_input = input(f"\n[第 {i} 次对话] 请输入提示词: ")

        # 执行模型推理
        response = llm(user_input)

        # 输出格式化结果
        print(f"\n[模型回复 {i}]", flush=True)
        print("-" * 40, flush=True)
        print(response, flush=True)
        print("-" * 40, flush=True)
