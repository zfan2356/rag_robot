import pytest

from config import ModelConfig, ModelConfigManager


def test_config_structure():
    mm = ModelConfigManager()
    mm.load()

    # 验证列表结构和类型
    assert len(mm.models) == 2
    assert mm.check("deepseek-r1:7b") == True
    assert mm.check("unknown-model") == False
