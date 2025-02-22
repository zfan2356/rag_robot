from typing import Any, List, Optional

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import Generation, LLMResult
from pydantic import BaseModel, Field

from config import ModelConfig, ModelConfigManager


class LocalBaseLLM(BaseLLM, BaseModel):
    base_url: str
    model: ModelConfig
    temperature: float
    top_p: float

    def __init__(
        self,
        model: ModelConfig,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ):
        """
        初始化本地基础LLM

        :param model: 模型配置对象
        :param base_url: Ollama服务器地址，默认http://localhost:11434
        :param temperature: 生成温度（0-1），默认0.7
        :param top_p: 核采样概率（0-1），默认0.9
        """
        super().__init__(
            base_url=base_url,
            model=model,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )

        # 参数验证
        if not 0 <= temperature <= 1:
            raise ValueError("temperature 必须在 0 到 1 之间")
        if not 0 <= top_p <= 1:
            raise ValueError("top_p 必须在 0 到 1 之间")

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
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
