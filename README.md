# rag_robot
a easy chat bot based on llm local inference and rag

一. 方案一

1 . 通过ollama下载本地模型

``` shell
ollama run deepseek-r1:7b
```

curl验证一下接口

```shell
curl http://localhost:11434/api/generate -d '{
  "model":"deepseek-r1:7b",
  "prompt":"你好",
  "stream":false
}'
```

2 . 构建RAG知识库

2.1 知识库准备

准备文档，然后使用Huggingface下的Embedding模型
```shell
ollama run nomic-embed-text
```

向量数据库可以选择FAISS/Chroma

2.2 RAG框架选择

例如RAGFLow, 然后配置模型路径指向ollama正在运行的本地模型

```shell
{
  "ChatModels": [{
    "model": "DeepSeek-R1",
    "api_base": "http://localhost:11434"
  }]
}
```

或者直接langchain自定义开发

```python
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS

# 初始化模型
llm = ChatOllama(model="deepseek-r1:7b", temperature=0)

# 加载文档并向量化
documents = load_your_files()  # 自定义文档加载
embeddings = HuggingFaceEmbeddings()  # 或OllamaEmbeddings
vectorstore = FAISS.from_documents(documents, embeddings)

# 构建检索链
retriever = vectorstore.as_retriever()
qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
```

3 . 构建ChatBot

可以选择使用gradio, 来快速搭建前端页面
