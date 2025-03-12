import os
from datetime import datetime

import pytest

from src.dao.documents import Document, DocumentDAO


@pytest.fixture
def dao():
    """创建 DAO 测试实例"""
    dao_instance = DocumentDAO()
    yield dao_instance

    # 测试后清理数据
    session = dao_instance.Session()
    try:
        # 只删除测试样本数据
        session.query(Document).filter(Document.title == "测试文档").delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def sample_doc():
    """示例文档数据"""
    return {"doc": "这是一个测试文档的内容", "title": "测试文档"}


def test_create_document(dao, sample_doc):
    """测试创建文档"""
    # 测试成功创建
    doc_id = dao.create(doc=sample_doc["doc"], title=sample_doc["title"])

    assert doc_id is not None
    assert isinstance(doc_id, int)
    assert doc_id > 0


def test_get_document(dao, sample_doc):
    """测试获取文档"""
    # 先创建文档
    doc_id = dao.create(doc=sample_doc["doc"], title=sample_doc["title"])

    # 测试获取存在的文档
    doc = dao.get(doc_id)
    assert doc is not None
    assert doc["doc"] == sample_doc["doc"]
    assert doc["title"] == sample_doc["title"]

    # 测试获取不存在的文档
    assert dao.get(9999) is None


def test_update_document(dao, sample_doc):
    """测试更新文档"""
    # 先创建文档
    doc_id = dao.create(doc=sample_doc["doc"], title=sample_doc["title"])

    # 准备更新数据
    new_doc = "更新后的文档内容"
    new_title = "更新后的标题"

    # 测试更新存在的文档
    assert dao.update(document_id=doc_id, doc=new_doc, title=new_title) is True

    # 验证更新结果
    updated = dao.get(doc_id)
    assert updated["doc"] == new_doc
    assert updated["title"] == new_title

    # 测试部分更新
    assert dao.update(document_id=doc_id, title="仅更新标题") is True

    partially_updated = dao.get(doc_id)
    assert partially_updated["title"] == "仅更新标题"
    assert partially_updated["doc"] == new_doc  # 其他字段保持不变

    # 测试更新不存在的文档
    assert dao.update(document_id=9999, title="不存在的文档") is False


def test_delete_document(dao, sample_doc):
    """测试删除文档"""
    # 先创建文档
    doc_id = dao.create(doc=sample_doc["doc"], title=sample_doc["title"])

    # 测试删除存在的文档
    assert dao.delete(doc_id) is True
    assert dao.get(doc_id) is None

    # 测试删除不存在的文档
    assert dao.delete(9999) is False


def test_list_documents(dao, sample_doc):
    """测试文档列表"""
    # 创建测试文档
    dao.create(doc=sample_doc["doc"], title=sample_doc["title"])
    dao.create(doc="另一个文档", title="标题2")

    # 测试获取所有文档
    all_docs = dao.list_all()
    assert len(all_docs) >= 2
    for doc in all_docs:
        assert "id" in doc
        assert "title" in doc
        assert "doc_preview" in doc
        assert "created_at" in doc
        assert "updated_at" in doc


def test_search_documents(dao, sample_doc):
    """测试搜索文档"""
    # 创建测试文档
    dao.create(doc="包含关键词的文档内容", title="测试搜索")

    # 测试关键词搜索
    keyword_results = dao.search_documents(keyword="关键词")
    assert len(keyword_results) > 0

    # 测试空关键词搜索
    all_results = dao.search_documents()
    assert len(all_results) > 0


def test_document_count(dao, sample_doc):
    """测试文档计数"""
    # 创建测试文档
    dao.create(doc=sample_doc["doc"], title=sample_doc["title"])
    dao.create(doc="另一个文档", title="标题2")

    # 获取计数
    counts = dao.get_document_count()
    assert isinstance(counts, dict)
    assert "total" in counts
    assert counts["total"] >= 2
