import abc
from typing import Any, Generic, List, TypeVar

import gradio as gr

from src.config import ModelConfig, ModelConfigManager
from src.dao.documents import DocumentDAO
from src.llm.prompt import PromptManager

T = TypeVar("T")


class RefFunc(Generic[T], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, dropdown: T):
        pass


class RefTemplateFunc(RefFunc[List[gr.Dropdown]]):
    def __call__(self, dropdown: List[gr.Dropdown]):
        prompt_manager = PromptManager()
        templates = prompt_manager.list_templates()

        dropdown[0].choices = [
            (
                f"{template['id']}: {template['name']}",
                f"{template['id']}: {template['name']}",
            )
            for template in templates
        ]


class RefModelConfigFunc(RefFunc[List[gr.Dropdown]]):
    def __call__(self, dropdown: List[gr.Dropdown]):
        model_config_manager = ModelConfigManager()
        model_config_manager.load()

        dropdown[0].choices = [
            (model_config.name, model_config.name)
            for model_config in model_config_manager.models
        ]
