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
        session.query(Document).filter(Document.user == "test_user").delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def sample_doc():
    """示例文档数据"""
    return {
        "user": "test_user",
        "doc": "这是一个测试文档的内容",
        "title": "测试文档",
        "source": "测试来源",
        "doc_type": "text",
        "metadata": {"key": "value"},
    }


def test_create_document(dao, sample_doc):
    """测试创建文档"""
    # 测试成功创建
    doc_id = dao.create(
        user=sample_doc["user"],
        doc=sample_doc["doc"],
        title=sample_doc["title"],
        source=sample_doc["source"],
        doc_type=sample_doc["doc_type"],
        metadata=sample_doc["metadata"],
    )

    assert doc_id is not None
    assert isinstance(doc_id, int)
    assert doc_id > 0


def test_get_document(dao, sample_doc):
    """测试获取文档"""
    # 先创建文档
    doc_id = dao.create(
        user=sample_doc["user"], doc=sample_doc["doc"], title=sample_doc["title"]
    )

    # 测试获取存在的文档
    doc = dao.get(doc_id)
    assert doc is not None
    assert doc["user"] == sample_doc["user"]
    assert doc["doc"] == sample_doc["doc"]
    assert doc["title"] == sample_doc["title"]

    # 测试获取不存在的文档
    assert dao.get(9999) is None


def test_update_document(dao, sample_doc):
    """测试更新文档"""
    # 先创建文档
    doc_id = dao.create(
        user=sample_doc["user"], doc=sample_doc["doc"], title=sample_doc["title"]
    )

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
    doc_id = dao.create(user=sample_doc["user"], doc=sample_doc["doc"])

    # 测试软删除
    assert dao.delete(doc_id) is True
    assert dao.get(doc_id) is None

    # 测试硬删除
    assert dao.hard_delete(doc_id) is True
    assert dao.get(doc_id) is None

    # 测试删除不存在的文档
    assert dao.delete(9999) is False
    assert dao.hard_delete(9999) is False


def test_list_documents(dao, sample_doc):
    """测试文档列表"""
    # 创建测试文档
    dao.create(user=sample_doc["user"], doc=sample_doc["doc"], is_processed=True)
    dao.create(user=sample_doc["user"], doc="未处理的文档", is_processed=False)

    # 测试获取所有文档
    all_docs = dao.list_all()
    assert len(all_docs) >= 2

    # 测试获取已处理文档
    processed_docs = dao.list_all(processed_only=True)
    assert all(doc["is_processed"] for doc in processed_docs)

    # 测试获取未处理文档
    unprocessed_docs = dao.list_all(processed_only=False)
    assert all(not doc["is_processed"] for doc in unprocessed_docs)


def test_get_by_user(dao, sample_doc):
    """测试获取用户文档"""
    # 创建测试文档
    dao.create(user=sample_doc["user"], doc=sample_doc["doc"])
    dao.create(user="other_user", doc="其他用户的文档")

    # 测试获取特定用户的文档
    user_docs = dao.get_by_user(sample_doc["user"])
    assert all(doc["user"] == sample_doc["user"] for doc in user_docs)


def test_search_documents(dao, sample_doc):
    """测试搜索文档"""
    # 创建测试文档
    dao.create(
        user=sample_doc["user"],
        doc="包含关键词的文档内容",
        title="测试搜索",
        doc_type="text",
    )

    # 测试关键词搜索
    keyword_results = dao.search_documents(keyword="关键词")
    assert len(keyword_results) > 0

    # 测试按类型搜索
    type_results = dao.search_documents(doc_type="text")
    assert all(doc["doc_type"] == "text" for doc in type_results)

    # 测试按用户搜索
    user_results = dao.search_documents(user=sample_doc["user"])
    assert all(doc["user"] == sample_doc["user"] for doc in user_results)


def test_mark_as_processed(dao, sample_doc):
    """测试标记文档为已处理"""
    # 创建未处理的文档
    doc_id = dao.create(
        user=sample_doc["user"], doc=sample_doc["doc"], is_processed=False
    )

    # 标记为已处理
    assert dao.mark_as_processed(doc_id) is True

    # 验证状态
    doc = dao.get(doc_id)
    assert doc["is_processed"] is True


def test_document_count(dao, sample_doc):
    """测试文档计数"""
    # 创建测试文档
    dao.create(user=sample_doc["user"], doc=sample_doc["doc"], is_processed=True)
    dao.create(user=sample_doc["user"], doc="未处理文档", is_processed=False)

    # 获取计数
    counts = dao.get_document_count()
    assert isinstance(counts, dict)
    assert "total" in counts
    assert "processed" in counts
    assert "unprocessed" in counts
    assert counts["total"] == counts["processed"] + counts["unprocessed"]
