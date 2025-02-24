from unittest.mock import Mock, patch

import pytest
import requests

from src.config import ModelConfigManager
from src.llm import LocalBaseLLM, OllamaManager


def test_service_available_and_model_exists():
    om = OllamaManager()

    result = om.check_status()

    print(result)

    assert result["service_available"] is True
    assert result["model_available"] is True
    assert "deepseek-r1:7b" in result["local_models"]
    assert "服务运行正常" in result["detail"]

    assert om.change_target_model("llama3.2:latest") == True


def test_start_service():
    om = OllamaManager()

    assert om.start_service() == True

    local_llm = LocalBaseLLM(ModelConfigManager().get_model())

    print(local_llm("hello"))


def test_ensure_model():
    om = OllamaManager("deepseek-r1:7b")

    assert om.ensure_model() == True
