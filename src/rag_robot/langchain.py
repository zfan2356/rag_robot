import os
from langchain_community.llms import OpenAI

# 配置OpenAI API密钥
os.environ["OPENAI_API_KEY"] = "sk-your-api-key-here"  # 替换为真实密钥

def main():
    # 初始化模型
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",  # 使用正确的模型名称
        temperature=0.7,
        max_tokens=150
    )
    
    # 简单调用示例
    response = llm.invoke("用一句话解释量子纠缠")
    print("模型回复：", response)
    
    # 带格式的复杂调用
    complex_response = llm.generate([
        "写一首关于春天的五言绝句",
        "将'Hello World'翻译成法语"
    ])
    
    print("\n诗歌创作：", complex_response.generations[0][0].text)
    print("法语翻译：", complex_response.generations[1][0].text)

if __name__ == "__main__":
    main()
