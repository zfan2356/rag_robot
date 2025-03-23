import logging
import traceback
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.bot_app.schemas.document import (
    DocumentCountResponse,
    DocumentCreate,
    DocumentPreviewResponse,
    DocumentResponse,
    DocumentUpdate,
)
from src.dao.documents import DocumentDAO

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        logger.info("Creating new document")
        dao = DocumentDAO()
        doc_data = document.model_dump()
        doc_id = dao.create(**doc_data)
        logger.info(f"Document created successfully with id: {doc_id}")
        return dao.get(doc_id)
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@router.get("/list", response_model=List[DocumentPreviewResponse])
def list_documents(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(100, description="返回的最大记录数"),
):
    """
    获取所有文档列表（带预览）
    """
    try:
        logger.info("Listing all documents")
        dao = DocumentDAO()
        documents = dao.list_all()
        logger.info(f"Found {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@router.get("/count", response_model=DocumentCountResponse)
def get_document_count():
    """
    获取文档总数
    """
    try:
        logger.info("Getting document count")
        dao = DocumentDAO()
        count = dao.get_document_count()
        logger.info(f"Document count: {count}")
        return count
    except Exception as e:
        logger.error(
            f"Error getting document count: {str(e)}\n{traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@router.get("/search", response_model=List[DocumentPreviewResponse])
def search_documents(keyword: str = Query(..., description="搜索关键词")):
    """
    搜索文档
    """
    try:
        logger.info(f"Searching documents with keyword: {keyword}")
        dao = DocumentDAO()
        documents = dao.search_documents(keyword)
        logger.info(f"Found {len(documents)} documents matching keyword")
        return documents
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int):
    """
    根据ID获取文档
    """
    try:
        logger.info(f"Getting document with id: {document_id}")
        dao = DocumentDAO()
        document = dao.get(document_id)
        if not document:
            logger.warning(f"Document not found with id: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        logger.info("Document found successfully")
        return document
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, document: DocumentUpdate):
    """
    更新文档
    """
    try:
        logger.info(f"Updating document with id: {document_id}")
        dao = DocumentDAO()
        existing_document = dao.get(document_id)
        if not existing_document:
            logger.warning(f"Document not found with id: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        update_data = document.model_dump(exclude_unset=True)
        if not update_data:
            logger.warning("No fields to update")
            raise HTTPException(status_code=400, detail="No fields to update")

        dao.update(document_id, **update_data)
        logger.info("Document updated successfully")
        return dao.get(document_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@router.delete("/{document_id}", response_model=dict)
def delete_document(document_id: int):
    """
    删除文档
    """
    try:
        logger.info(f"Deleting document with id: {document_id}")
        dao = DocumentDAO()
        existing_document = dao.get(document_id)
        if not existing_document:
            logger.warning(f"Document not found with id: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        dao.delete(document_id)
        logger.info("Document deleted successfully")
        return {"message": "Document deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )
