# rag_robot
a easy chat bot based on llm local inference and rag

## 一. Solution 1

### 1 . Download Local Model via Ollama

``` shell
ollama run deepseek-r1:7b
```
Verify model download status:

```shell
ollama list
```
Ollama services typically run on port 11434. To test the API locally:

```shell
curl http://localhost:11434/api/generate -d '{
  "model":"deepseek-r1:7b",
  "prompt":"你好",
  "stream":false
}'
```

Check available models:

```shell
curl http://localhost:11434/api/tags
```

(Refer to Ollama official documentation for more APIs)

### 2 . Build RAG Knowledge Base

2.1 Knowledge Base Preparation

Prepare documents, Use Hugging Face's embedding models:

```shell
ollama run nomic-embed-text
```

Choose vector databases like FAISS/Chroma

2.2 RAG Framework Options

Option 1: Use RAGFlow (configure model endpoint in settings):

```shell
{
  "ChatModels": [{
    "model": "DeepSeek-R1",
    "api_base": "http://localhost:11434"
  }]
}
```

Option 2: Custom development with LangChain:

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

### 3. DataBase

choose mysql, and create two tables:

- **prompt_template_table**: manage custom prompt templates by users.

- **document_table**: stores RAG-based documents uploaded by users.


### 4 . Build ChatBot Interface

Use Gradio for rapid frontend development?


### 5. Docker

Use Dockerfile to build the backend application.

```shell
# build
docker build -t rag_robot -f Dockerfile .
# run backend app image
docker run -it -p 8000:8000 rag_robot
```
you can visit `http://0.0.0.0:8000/docs` to test if it works properly

Additionally, docker/docker-compose.yml can be used to build containers including MySQL.

```shell
docker-compose -f docker/docker-compose.yml up -d

# 停止所有服务
docker-compose -f docker/docker-compose.yml stop

# 启动所有服务
docker-compose -f docker/docker-compose.yml start

# 重启所有服务
docker-compose -f docker/docker-compose.yml restart

# 停止并删除所有服务（包括网络，但不包括数据卷）
docker-compose -f docker/docker-compose.yml down
```

use the above commands to run container, you can run `docker ps` to check if composed container is running


### TODO:

llm: 完成了基本功能，可以做到流式回复与普通回复，并且支持 | 链式调用
prompt: 已经调通了链式调用，但是与dao层的交互还没测试
fastapi：还没集成prompt 接口
