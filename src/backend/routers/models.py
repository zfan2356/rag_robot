from fastapi import APIRouter, Depends, HTTPException

from src.backend.schemas.model import ModelResponse
from src.backend.utils import get_logger
from src.config import ModelConfigManager

router = APIRouter(prefix="/models", tags=["models"])
logger = get_logger()

# 初始化配置管理器和FastAPI应用
config_manager = ModelConfigManager()


@router.get("/", response_model=list[ModelResponse])
def list_models():
    """获取所有可用模型"""
    return config_manager.models


@router.get("/{model_name}", response_model=ModelResponse)
async def get_model(model_name: str):
    """获取指定模型详情"""
    model = config_manager.get_model(model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/check/{model_name}")
async def check_model(model_name: str):
    """检查模型是否存在"""
    exists = config_manager.check(model_name)
    return {"exists": exists, "model_name": model_name}
