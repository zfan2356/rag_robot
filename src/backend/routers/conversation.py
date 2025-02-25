from fastapi import APIRouter, Depends, HTTPException
from langchain.chains.llm import LLMChain
from langchain.memory import ConversationBufferMemory
from starlette.responses import StreamingResponse

from src.backend.schemas import *
from src.backend.utils import get_logger
from src.config import ModelConfigManager
from src.llm import AsyncLocalBaseLLM

router = APIRouter(prefix="/conversation", tags=["conversation"])
logger = get_logger()

# 初始化配置管理器和FastAPI应用
config_manager = ModelConfigManager()
memory = ConversationBufferMemory()


@router.get("/{model_name}")
async def generate(model_name: str, prompt: str):
    exists = config_manager.check(model_name)
    if not exists:
        raise HTTPException(status_code=404, detail="Model not found")

    asyncLLM = AsyncLocalBaseLLM(model=config_manager.get_model(model_name))
    raw_gen = asyncLLM._astream(
        prompt=prompt,
        stop=["\n"],
    )

    return StreamingResponse(
        content=raw_gen,
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"},
    )
