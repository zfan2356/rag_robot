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

llm = ChatOllama(model="deepseek-r1:7b", temperature=0)

documents = load_your_files()
embeddings = HuggingFaceEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

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

Use Gradio for rapid frontend development and prototyping.

Implement React for comprehensive CRUD (Create, Read, Update, Delete) functionality for documents, prompts, and model configurations.

The Gradio interface will be embedded within the React application as an iframe at the root URL.


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
docker-compose -f docker/docker-compose.yml up -d --build app
```
use the above commands to run container, you can run `docker ps` to check if composed container is running


### Finally: How to use?

1. start mysql docker and fast api service

```shell
docker-compose -f docker/docker-compose.yml up --build app
uvicorn src.bot_app.app:app --reload
```

2. download ollama language models and embedding models
```shell
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text
ollama pull llama3.2:latest
```

3. start gradio service

```shell
python -m gr_app.web_demo
```

4. start react frontend service

```shell
npm install 
npm run dev
```
ß