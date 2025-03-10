from typing import List

from pydantic import BaseModel

from src.config import ModelConfig


class ListModelResponse(BaseModel):
    models: List[ModelConfig]


class GetModelResponse(BaseModel):
    model: ModelConfig


class CheckModelResponse(BaseModel):
    exists: bool
