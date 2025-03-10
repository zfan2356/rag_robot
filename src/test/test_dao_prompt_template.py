import os
from datetime import datetime

import pytest

from src.dao.prompt import PromptDAO, PromptTemplate

DB_CONFIG = {
    "user": "root",
    "password": "123456",
    "host": "localhost",
    "database": "rag_robot",
}

DB_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"


@pytest.fixture(scope="session")
def setup_test_db():
    """设置测试数据库"""
    import pymysql

    # 连接 MySQL 服务器（不指定数据库）
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )

    try:
        with conn.cursor() as cursor:
            # 创建测试数据库
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def dao(setup_test_db):
    """创建 DAO 测试实例"""
    dao_instance = PromptDAO(db_url=DB_URL)
    yield dao_instance

    # 测试后清理数据
    session = dao_instance.Session()
    try:
        session.query(PromptTemplate).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def sample_template():
    """示例模板数据"""
    return {
        "template_id": "test-template",
        "name": "测试模板",
        "description": "这是一个测试模板",
        "template_content": [
            ("system", "你是一个测试助手"),
            ("human", "{input}"),
            ("placeholder", "{chat_history}"),
        ],
    }


def test_create_template(dao, sample_template):
    """测试创建模板"""
    # 测试成功创建
    assert (
        dao.create(
            template_id=sample_template["template_id"],
            name=sample_template["name"],
            description=sample_template["description"],
            template_content=sample_template["template_content"],
        )
        is True
    )

    # 测试重复创建
    assert (
        dao.create(
            template_id=sample_template["template_id"],
            name=sample_template["name"],
            description=sample_template["description"],
            template_content=sample_template["template_content"],
        )
        is False
    )


def test_get_template(dao, sample_template):
    """测试获取模板"""
    # 先创建模板
    dao.create(
        template_id=sample_template["template_id"],
        name=sample_template["name"],
        description=sample_template["description"],
        template_content=sample_template["template_content"],
    )

    # 测试获取存在的模板
    template = dao.get(sample_template["template_id"])
    assert template is not None
    assert template["template_id"] == sample_template["template_id"]
    assert template["name"] == sample_template["name"]
    assert template["description"] == sample_template["description"]
    assert template["template_content"] == sample_template["template_content"]
    assert isinstance(template["created_at"], datetime)
    assert isinstance(template["updated_at"], datetime)

    # 测试获取不存在的模板
    assert dao.get("non-existent-template") is None


def test_update_template(dao, sample_template):
    """测试更新模板"""
    # 先创建模板
    dao.create(
        template_id=sample_template["template_id"],
        name=sample_template["name"],
        description=sample_template["description"],
        template_content=sample_template["template_content"],
    )

    # 准备更新数据
    new_content = [("system", "你是一个更新后的测试助手"), ("human", "{input}")]
    new_name = "更新后的测试模板"
    new_description = "这是更新后的测试模板"

    # 测试更新存在的模板
    assert (
        dao.update(
            template_id=sample_template["template_id"],
            template_content=new_content,
            name=new_name,
            description=new_description,
        )
        is True
    )

    # 验证更新结果
    updated = dao.get(sample_template["template_id"])
    assert updated["name"] == new_name
    assert updated["description"] == new_description
    assert updated["template_content"] == new_content

    # 测试更新不存在的模板
    assert (
        dao.update(template_id="non-existent-template", template_content=new_content)
        is False
    )


def test_delete_template(dao, sample_template):
    """测试删除模板"""
    # 先创建模板
    dao.create(
        template_id=sample_template["template_id"],
        name=sample_template["name"],
        description=sample_template["description"],
        template_content=sample_template["template_content"],
    )

    # 测试删除存在的模板
    assert dao.delete(sample_template["template_id"]) is True
    assert dao.get(sample_template["template_id"]) is None

    # 测试删除不存在的模板
    assert dao.delete("non-existent-template") is False


def test_list_all_templates(dao, sample_template):
    """测试列出所有模板"""
    # 初始状态应该为空
    assert len(dao.list_all()) == 0

    # 创建多个模板
    templates = [
        {
            "template_id": "template-1",
            "name": "模板1",
            "description": "这是模板1",
            "template_content": [("system", "系统1"), ("human", "{input}")],
        },
        {
            "template_id": "template-2",
            "name": "模板2",
            "description": "这是模板2",
            "template_content": [("system", "系统2"), ("human", "{input}")],
        },
    ]

    for template in templates:
        dao.create(
            template_id=template["template_id"],
            name=template["name"],
            description=template["description"],
            template_content=template["template_content"],
        )

    # 验证列表结果
    all_templates = dao.list_all()
    assert len(all_templates) == 2

    # 验证返回的模板数据是否完整
    for template in all_templates:
        assert "template_id" in template
        assert "name" in template
        assert "description" in template
        assert "template_content" in template
        assert "created_at" in template
        assert "updated_at" in template


def test_template_timestamps(dao, sample_template):
    """测试时间戳更新"""
    # 创建模板
    dao.create(
        template_id=sample_template["template_id"],
        name=sample_template["name"],
        description=sample_template["description"],
        template_content=sample_template["template_content"],
    )

    # 获取初始时间戳
    template = dao.get(sample_template["template_id"])
    created_at = template["created_at"]
    updated_at = template["updated_at"]

    # 等待一小段时间后更新
    import time

    time.sleep(1)

    # 更新模板
    dao.update(
        template_id=sample_template["template_id"],
        template_content=[("system", "新系统提示"), ("human", "{input}")],
    )

    # 检查时间戳
    updated_template = dao.get(sample_template["template_id"])
    assert updated_template["created_at"] == created_at  # 创建时间不变
    assert updated_template["updated_at"] > updated_at  # 更新时间变化
