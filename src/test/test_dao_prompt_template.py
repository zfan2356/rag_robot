import os
from datetime import datetime

import pytest

from src.dao.prompt import PromptDAO, PromptTemplate


@pytest.fixture
def dao():
    """创建 DAO 测试实例"""
    dao_instance = PromptDAO()
    yield dao_instance

    # 测试后清理数据
    session = dao_instance.Session()
    try:
        # 只删除测试样本数据，保留其他数据
        session.query(PromptTemplate).filter(
            PromptTemplate.name == "测试助手模板"
        ).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def sample_template():
    """示例模板数据"""
    return {
        "system_prompt": "你是一个专业的AI助手，擅长回答各类问题。请保持友好和专业的态度，给出准确和有帮助的回答。",
        "name": "测试助手模板",
        "description": "这是一个用于测试的助手模板",
    }


def test_create_template(dao, sample_template):
    """测试创建模板"""
    # 测试成功创建
    template_id = dao.create(
        system_prompt=sample_template["system_prompt"],
        name=sample_template["name"],
        description=sample_template["description"],
    )

    assert template_id is not None
    assert isinstance(template_id, int)
    assert template_id > 0


def test_get_template(dao):
    """测试获取模板"""
    # 获取所有模板并写入文件
    templates = dao.list_all()
    with open(
        "/Users/zhangfan/zfan2356/github/rag_robot/src/test/output.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n当前数据库中的所有模板:\n")
        for template in templates:
            f.write(f"\nID: {template['id']}\n")
            f.write(f"名称: {template['name'].encode('utf-8').decode('utf-8')}\n")
            f.write(
                f"描述: {template['description'].encode('utf-8').decode('utf-8')}\n"
            )
            f.write(
                f"系统提示词: {template['system_prompt'].encode('utf-8').decode('utf-8')}\n"
            )
            f.write(f"创建时间: {template['created_at']}\n")
            f.write(f"更新时间: {template['updated_at']}\n")


def test_update_template(dao, sample_template):
    """测试更新模板"""
    # 先创建模板
    template_id = dao.create(
        system_prompt=sample_template["system_prompt"],
        name=sample_template["name"],
        description=sample_template["description"],
    )

    # 准备更新数据
    new_system_prompt = "你是一个更新后的AI助手，专注于提供技术支持。"
    new_name = "更新后的测试模板"
    new_description = "这是更新后的测试模板描述"

    # 测试更新存在的模板
    assert (
        dao.update(
            template_id=template_id,
            system_prompt=new_system_prompt,
            name=new_name,
            description=new_description,
        )
        is True
    )

    # 验证更新结果
    updated = dao.get(template_id)
    assert updated["system_prompt"] == new_system_prompt
    assert updated["name"] == new_name
    assert updated["description"] == new_description

    # 测试部分更新
    assert dao.update(template_id=template_id, name="仅更新名称") is True

    partially_updated = dao.get(template_id)
    assert partially_updated["name"] == "仅更新名称"
    assert partially_updated["system_prompt"] == new_system_prompt  # 其他字段保持不变

    # 测试更新不存在的模板
    assert dao.update(template_id=9999, name="不存在的模板") is False


def test_delete_template(dao, sample_template):
    """测试删除模板"""
    # 先创建模板
    template_id = dao.create(
        system_prompt=sample_template["system_prompt"],
        name=sample_template["name"],
        description=sample_template["description"],
    )

    # 测试删除存在的模板
    assert dao.delete(template_id) is True

    # 验证删除后无法获取
    assert dao.get(template_id) is None

    # 测试删除不存在的模板
    assert dao.delete(9999) is False


def test_get_by_name(dao, sample_template):
    """测试通过名称获取模板"""
    # 创建模板
    dao.create(
        system_prompt=sample_template["system_prompt"],
        name="特定名称模板",
        description="通过名称查找的测试模板",
    )

    # 测试通过名称查找
    template = dao.get_by_name("特定名称模板")
    assert template is not None
    assert template["name"] == "特定名称模板"

    # 测试查找不存在的名称
    assert dao.get_by_name("不存在的模板名称") is None


def test_template_timestamps(dao, sample_template):
    """测试时间戳更新"""
    # 创建模板
    template_id = dao.create(
        system_prompt=sample_template["system_prompt"], name=sample_template["name"]
    )

    # 获取初始时间戳
    template = dao.get(template_id)
    created_at = template["created_at"]
    updated_at = template["updated_at"]

    # 等待一小段时间后更新
    import time

    time.sleep(1)

    # 更新模板
    dao.update(template_id=template_id, system_prompt="新的系统提示词")

    # 检查时间戳
    updated_template = dao.get(template_id)
    assert updated_template["created_at"] == created_at  # 创建时间不变
    assert updated_template["updated_at"] > updated_at  # 更新时间变化
