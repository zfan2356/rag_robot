from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """文档基础模型"""

    doc: str = Field(..., description="文档内容")
    title: Optional[str] = Field(None, description="文档标题")


class DocumentCreate(DocumentBase):
    """创建文档的请求模型"""

    pass


class DocumentUpdate(BaseModel):
    """更新文档的请求模型"""

    doc: Optional[str] = Field(None, description="文档内容")
    title: Optional[str] = Field(None, description="文档标题")


class DocumentResponse(DocumentBase):
    """文档的响应模型"""

    id: int = Field(..., description="文档ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


class DocumentPreviewResponse(BaseModel):
    """文档预览的响应模型"""

    id: int = Field(..., description="文档ID")
    title: Optional[str] = Field(None, description="文档标题")
    doc_preview: str = Field(..., description="文档内容预览")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


class DocumentCountResponse(BaseModel):
    """文档统计信息的响应模型"""

    total: int = Field(..., description="文档总数")
