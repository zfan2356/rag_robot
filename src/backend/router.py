from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config.config import ModelConfigManager

# 初始化配置管理器和FastAPI应用
config_manager = ModelConfigManager()
app = FastAPI(title="Model API", version="0.1.0")


class ModelResponse(BaseModel):
    name: str
    id: str
    size: str


@app.get("/models", response_model=list[ModelResponse])
def list_models():
    """获取所有可用模型"""
    return config_manager.models


@app.get("/models/{model_name}", response_model=ModelResponse)
def get_model(model_name: str):
    """获取指定模型详情"""
    model = config_manager.get_model(model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.get("/models/check/{model_name}")
def check_model(model_name: str):
    """检查模型是否存在"""
    exists = config_manager.check(model_name)
    return {"exists": exists, "model_name": model_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
