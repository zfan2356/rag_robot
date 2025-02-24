import inspect

import pytest
from langchain_core.language_models import BaseLLM

from src.config import ModelConfig
from src.llm import AsyncLocalBaseLLM


@pytest.mark.asyncio
async def test_async_llm():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")

    llm = AsyncLocalBaseLLM(
        model=model_config,
    )

    async for chunk in llm._astream(prompt="hello", stop=["\n"]):
        print(chunk)
