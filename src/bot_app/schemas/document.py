from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentBase(BaseModel):
    """文档基础模型"""

    title: Optional[str] = None
    doc: str


class DocumentCreate(DocumentBase):
    """创建文档请求模型"""

    pass


class DocumentUpdate(BaseModel):
    """更新文档请求模型"""

    title: Optional[str] = None
    doc: Optional[str] = None


class DocumentResponse(DocumentBase):
    """文档响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentPreviewResponse(BaseModel):
    """文档预览响应模型"""

    id: int
    title: Optional[str] = None
    doc_preview: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentCountResponse(BaseModel):
    """文档计数响应模型"""

    total: int
