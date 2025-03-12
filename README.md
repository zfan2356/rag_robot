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

```shell
docker exec -it mysql mysql -uroot -p123456
```



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
# remove
docker-compose -f docker/docker-compose.yml down
# remove containers and volumes
docker-compose -f docker/docker-compose.yml down -v

# create and start service
docker-compose -f docker/docker-compose.yml up -d
```
use the above commands to run container, you can run `docker ps` to check if composed container is running


### TODO:

llm: 基本功能√，流式回复与普通回复√，支持 | 链式调用 √，test √

docker: compose √，init mysql √

prompt: 链式调用√，dao层交互√， test √

docs: dao层交互 √， test √

context: √

RagRobotLLM: test todo

fastapi：

- model basic info： √
- model conversation：todo
- prompt crud: todo
- docs crud: todo
