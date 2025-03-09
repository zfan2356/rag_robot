from src.config import ModelConfig
from src.llm.llm import LocalBaseLLM
from src.llm.prompt import PromptManager


def test_hand_manage_prompt():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")
    llm = LocalBaseLLM(model=model_config)

    prompt = f"你现在是一个AI助手, 请根据用户的问题给出回答, 用户的问题如下: \n"
    for i in range(1, 4):
        # 获取用户输入
        user_input = input(f"\n[第 {i} 次对话] 请输入提示词: ")
        prompt += f"usr: {user_input}\n"
        # 执行模型推理
        response = ""
        for chunk in llm.stream(prompt):
            response += chunk
            print(chunk, end="", flush=True)
        prompt += f"model: {response}\n"
        # 输出格式化结果
        print(f"\n[模型回复 {i}]", flush=True)
        print("-" * 40, flush=True)


def test_langchain_manage_prompt():
    model_config = ModelConfig(name="deepseek-r1:7b", id="0a8c26691023", size="4.7 GB")
    llm = LocalBaseLLM(model=model_config)

    prompt_manager = PromptManager(llm)

    # 测试普通对话
    response = prompt_manager.generate_response("Python中如何实现单例模式？")
    print("普通对话响应:", response)

    # # 测试带历史记录的对话
    # history = [
    #     {"role": "user", "content": "什么是设计模式？"},
    #     {"role": "assistant", "content": "设计模式是软件开发中常见问题的最佳实践解决方案..."},
    # ]
    # response = prompt_manager.generate_response("给我一个例子", history)
    # print("\n带历史记录的对话响应:", response)

    # # 测试流式输出
    # print("\n流式输出测试:")
    # for chunk in prompt_manager.stream_response("解释一下装饰器模式"):
    #     print(chunk, end="", flush=True)
