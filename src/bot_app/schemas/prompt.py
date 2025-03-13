from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptTemplateBase(BaseModel):
    """提示词模板基础模型"""

    system_prompt: str = Field(..., description="系统提示词")
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")


class PromptTemplateCreate(PromptTemplateBase):
    """创建提示词模板的请求模型"""

    pass


class PromptTemplateUpdate(BaseModel):
    """更新提示词模板的请求模型"""

    system_prompt: Optional[str] = Field(None, description="系统提示词")
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")


class PromptTemplateResponse(PromptTemplateBase):
    """提示词模板的响应模型"""

    id: int = Field(..., description="模板ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )
