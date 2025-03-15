import pytest

from src.config import ModelConfig
from src.llm.context import ContextManager
from src.llm.llm import LocalBaseLLM, RagRobotLLM
from src.llm.prompt import PromptManager


@pytest.fixture
def context_manager():
    prompt_manager = PromptManager()
    return ContextManager(prompt_manager=prompt_manager, template_id=1)


@pytest.fixture
def local_llm():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")
    return LocalBaseLLM(model=model_config)


@pytest.fixture
def rag_robot(context_manager, local_llm):
    return RagRobotLLM(context_manager=context_manager, llm=local_llm)


def test_rag_robot_init(rag_robot):
    """测试RagRobotLLM初始化"""
    assert isinstance(rag_robot.context_manager, ContextManager)
    assert isinstance(rag_robot.llm, LocalBaseLLM)

def test_rag_robot_generate(rag_robot):
    """测试普通生成响应"""
    response = rag_robot.invoke("你好")
    assert isinstance(response, str)
    assert len(response) > 0
    
    # 将响应转换为JSON字符串并写入文件
    import json
    import os
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "output.txt")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json_response = json.dumps(response, ensure_ascii=False)
        f.write(json_response)


def test_rag_robot_stream_generate(rag_robot):
    """测试流式生成响应"""
    # 测试流式生成
    chunks = []
    for chunk in rag_robot.stream_generate("你好"):
        assert isinstance(chunk, str)
        chunks.append(chunk)

    assert len(chunks) > 0
    full_response = "".join(chunks)
    assert len(full_response) > 0


@pytest.mark.asyncio
async def test_rag_robot_agenerate(rag_robot):
    """测试异步生成响应"""
    # 测试异步生成
    response = await rag_robot.agenerate("你好")
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_rag_robot_astream_generate(rag_robot):
    """测试异步流式生成响应"""
    # 测试异步流式生成
    chunks = []
    async for chunk in rag_robot.astream_generate("你好"):
        assert isinstance(chunk, str)
        chunks.append(chunk)

    assert len(chunks) > 0
    full_response = "".join(chunks)
    assert len(full_response) > 0


def test_rag_robot_context_management(rag_robot):
    """测试上下文管理功能"""
    # 第一轮对话
    first_response = rag_robot.generate("我叫张三")
    assert isinstance(first_response, str)
    assert len(first_response) > 0

    # 第二轮对话，引用上下文
    second_response = rag_robot.generate("你还记得我的名字吗？请说出我的名字。")
    assert isinstance(second_response, str)
    assert len(second_response) > 0

    # 检查第二轮回复中是否包含"张三"（上下文信息）
    assert "张三" in second_response.lower() or "zhang san" in second_response.lower()


@pytest.mark.asyncio
async def test_rag_robot_async_context_management(rag_robot):
    """测试异步上下文管理功能"""
    # 第一轮对话
    first_response = await rag_robot.agenerate("首先请你记住我今年30岁")
    assert isinstance(first_response, str)
    assert len(first_response) > 0

    # 第二轮对话，引用上下文
    second_response = await rag_robot.agenerate("我的年龄是多少？")
    assert isinstance(second_response, str)
    assert len(second_response) > 0

    # 检查第二轮回复中是否包含"30"（上下文信息）
    assert "30" in second_response


def test_rag_robot_multi_turn_conversation(rag_robot):
    """测试多轮对话上下文管理"""
    # 第一轮对话
    rag_robot.generate("请记住苹果的得分是10")

    # 第二轮对话
    rag_robot.generate("请记住香蕉的得分是20")

    # 第三轮对话，引用前两轮的上下文
    third_response = rag_robot.generate("苹果和香蕉谁的得分更低？")

    # 检查第三轮回复中是否包含前两轮提到的水果
    assert "苹果" in third_response or "apple" in third_response.lower()


def test_rag_robot_clear_history(rag_robot):
    """测试清除历史记录功能"""
    # 生成一些对话历史
    rag_robot.generate("你好")
    rag_robot.generate("今天天气怎么样？")

    # 清除历史记录
    rag_robot.clear_history()

    # 验证清除后可以正常生成新的对话
    response = rag_robot.generate("你是谁？")
    assert isinstance(response, str)
    assert len(response) > 0
