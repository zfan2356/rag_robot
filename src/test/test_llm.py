import pytest

from src.config import ModelConfig
from src.llm import LocalBaseLLM


def test_local_llm():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")

    llm = LocalBaseLLM(
        model=model_config,
    )
    print(llm.invoke("hello"))
