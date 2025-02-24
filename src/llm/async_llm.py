import asyncio
import json
from abc import ABC
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Optional

import aiohttp
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import Generation, GenerationChunk, LLMResult
from pydantic import BaseModel, Field

from src.config import ModelConfig, ModelConfigManager


class AsyncLocalBaseLLM(BaseLLM, BaseModel):
    base_url: str
    model: ModelConfig
    temperature: float
    top_p: float
    session: Optional[aiohttp.ClientSession] = Field(default=None, exclude=True)

    def __init__(
        self,
        model: ModelConfig,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ):
        super().__init__(
            base_url=base_url,
            model=model,
            temperature=temperature,
            top_p=top_p,
            session=None,
            **kwargs,
        )

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
        async_run_manager = self._convert_run_manager(run_manager)

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self._agenerate(prompts, stop, async_run_manager, **kwargs)
        )

    def _convert_run_manager(
        self, sync_manager: Optional[CallbackManagerForLLMRun]
    ) -> Optional[AsyncCallbackManagerForLLMRun]:
        """转换同步回调管理器为异步版本"""
        return AsyncCallbackManagerForLLMRun(
            handlers=sync_manager.handlers if sync_manager else [],
            parent_run_id=sync_manager.parent_run_id if sync_manager else None,
        )

    async def _astream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        params = self._build_request_params(prompt, **kwargs)

        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.post(
            f"{self.base_url}/api/generate",
            json=params,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            response.raise_for_status()

            async for chunk in response.content:
                if not chunk:
                    continue

                data = json.loads(chunk)
                text = data.get("response", "")
                chunk = GenerationChunk(text=text)
                yield chunk

                if run_manager:
                    await run_manager.on_llm_new_token(token=text)

    def _build_request_params(self, prompt: str, **kwargs) -> Dict:
        return {
            "model": self.model.name,
            "prompt": prompt,
            "stream": True,
            "temperature": self.temperature,
            "top_p": self.top_p,
            **kwargs,
        }

    async def _agenerate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []

        async def process_prompt(prompt: str):
            chunks = []
            async for chunk in self._astream(prompt, stop, run_manager, **kwargs):
                chunks.append(chunk)
            return [Generation(text="".join(c.text for c in chunks))]

        tasks = [process_prompt(p) for p in prompts]
        results = await asyncio.gather(*tasks)

        return LLMResult(generations=results)

    @property
    def _llm_type(self) -> str:
        return "custom_async_ollama"

    async def aclose(self):
        if self.session:
            await self.session.close()
