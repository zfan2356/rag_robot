from langchain_community.llms import OpenAI
from langchain_core.chains import LLMChain

llm = OpenAI(model="DeepSeek-R1")  # 接入大模型
prompt_template = "回答关于{topic}的问题："  # 定义提示模板
chain = LLMChain(llm=llm, prompt=prompt_template)
print(chain.run("量子力学"))  # 输出生成结果