import pytest

from src.config import ModelConfig
from src.llm.llm import LocalBaseLLM


def test_local_llm():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")

    llm = LocalBaseLLM(
        model=model_config,
    )

    for chunk in llm.stream("你好"):
        print(chunk, end="", flush=True)


def test_local_llm_invoke():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")

    llm = LocalBaseLLM(
        model=model_config,
    )

    response = llm.invoke("你好")
    print(response)
