from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse

from src.backend.schemas import *
from src.backend.utils import get_logger
from src.config import ModelConfigManager
from src.llm import AsyncLocalBaseLLM

"""
查询model基本信息
"""
router = APIRouter(prefix="/models", tags=["models"])
logger = get_logger()

# 初始化配置管理器和FastAPI应用
config_manager = ModelConfigManager()


@router.get("/", response_model=ListModelResponse)
def list_models():
    """获取所有可用模型"""
    return ListModelResponse(models=config_manager.models)


@router.get("/{model_name}", response_model=GetModelResponse)
async def get_model(model_name: str):
    """获取指定模型详情"""
    model = config_manager.get_model(model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return GetModelResponse(model=model)


@router.get("/check/{model_name}", response_model=CheckModelResponse)
async def check_model(model_name: str):
    """检查模型是否存在"""
    exists = config_manager.check(model_name)
    return CheckModelResponse(
        exists=exists,
    )
