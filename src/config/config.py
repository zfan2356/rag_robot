from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel


class ModelConfig(BaseModel):
    name: str
    id: str
    size: str


class ModelConfigManager:
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化模型配置管理器
        :param config_path: 可选的配置文件路径，默认为同级目录下的models.yaml
        """
        self.config_path = config_path or Path(__file__).parent / "models.yaml"
        self.models: List[ModelConfig] = []
        self.load()

    def load(self) -> None:
        """加载并验证模型配置"""
        with open(self.config_path, "r") as f:
            config_data = yaml.safe_load(f)

        self.models = [ModelConfig(**item) for item in config_data]

    def check(self, model_name: str) -> bool:
        """
        检查指定模型名称是否存在
        :param model_name: 要检查的模型名称
        :return: 是否存在（布尔值）
        """
        return any(model.name == model_name for model in self.models)

    def get_model(self, model_name: Optional[str] = None) -> Optional[ModelConfig]:
        """
        获取指定名称的模型配置
        :param model_name: 要获取的模型名称
        :return: ModelConfig对象或None
        """
        if model_name is None:
            return self.models[0]

        for model in self.models:
            if model.name == model_name:
                return model
        return None
