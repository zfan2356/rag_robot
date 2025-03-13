from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.bot_app.schemas.document import (
    DocumentCountResponse,
    DocumentCreate,
    DocumentPreviewResponse,
    DocumentResponse,
    DocumentUpdate,
)
from src.dao.documents import DocumentDAO

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Document not found"}},
)


@router.post("/create", response_model=DocumentResponse)
def create_document(document: DocumentCreate):
    """
    创建新文档
    """
    dao = DocumentDAO()
    doc_data = document.model_dump()
    doc_id = dao.create(**doc_data)
    return dao.get(doc_id)


@router.get("/list", response_model=List[DocumentPreviewResponse])
def list_documents(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(100, description="返回的最大记录数"),
):
    """
    获取所有文档列表（带预览）
    """
    dao = DocumentDAO()
    documents = dao.list_all()
    return documents


@router.get("/count", response_model=DocumentCountResponse)
def get_document_count():
    """
    获取文档总数
    """
    dao = DocumentDAO()
    count = dao.get_document_count()
    return count


@router.get("/search", response_model=List[DocumentPreviewResponse])
def search_documents(keyword: str = Query(..., description="搜索关键词")):
    """
    搜索文档
    """
    dao = DocumentDAO()
    documents = dao.search_documents(keyword)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int):
    """
    根据ID获取文档
    """
    dao = DocumentDAO()
    document = dao.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, document: DocumentUpdate):
    """
    更新文档
    """
    dao = DocumentDAO()
    existing_document = dao.get(document_id)
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = document.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    dao.update(document_id, **update_data)
    return dao.get(document_id)


@router.delete("/{document_id}", response_model=dict)
def delete_document(document_id: int):
    """
    删除文档
    """
    dao = DocumentDAO()
    existing_document = dao.get(document_id)
    if not existing_document:
        raise HTTPException(status_code=404, detail="Document not found")

    dao.delete(document_id)
    return {"message": "Document deleted successfully"}
