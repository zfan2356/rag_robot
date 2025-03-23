import logging
from typing import Any, Dict, Generator, List, Optional, Tuple

from langchain_core.documents import Document as LangchainDocument
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig, RunnableMap, RunnablePassthrough

from src.config import ModelConfig, ModelConfigManager
from src.llm import LocalBaseLLM, RagRobotLLM
from src.llm.context import ContextManager
from src.llm.prompt import PromptManager
from src.rag.retriever import DocumentRetriever

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RagChain:
    """RAG链，用于将检索器和LLM结合起来"""

    def __init__(
        self,
        retriever: DocumentRetriever,
        model_name: str = "llama3.2:latest",
        template_id: int = 1,
    ):
        """初始化RAG链

        Args:
            retriever: 文档检索器
            model_name: 模型名称
            template_id: 提示词模板ID
        """
        self.retriever = retriever
        self.model_name = model_name
        self.template_id = template_id
        self._chain = None  # 缓存链
        self._llm = None  # 缓存LLM

    @property
    def llm(self):
        """获取LLM实例"""
        if self._llm is None:
            mm = ModelConfigManager()
            mm.load()
            model_config = mm.get_model(self.model_name)
            if not model_config:
                raise ValueError(f"模型配置不存在: {self.model_name}")

            self._llm = RagRobotLLM(
                context_manager=ContextManager(
                    prompt_manager=PromptManager(),
                    template_id=self.template_id,
                    is_rag_mode=True,
                ),
                llm=LocalBaseLLM(model=model_config),
            )
        return self._llm

    @property
    def chain(self):
        """获取RAG链"""
        if self._chain is None:
            self._chain = (
                RunnableMap({"context": self.retriever, "input": RunnablePassthrough()})
                | self._format_context
                | self.llm
                | StrOutputParser()
            )
        return self._chain

    def update_model(self, model_name: str):
        """更新模型名称"""
        self.model_name = model_name
        self._llm = None  # 清除缓存
        self._chain = None  # 清除缓存

    def update_template(self, template_id: int):
        """更新提示词模板ID"""
        self.template_id = template_id
        self._llm = None  # 清除缓存
        self._chain = None  # 清除缓存

    def _format_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """格式化上下文信息

        Args:
            inputs: 输入字典，包含context和input

        Returns:
            Dict[str, Any]: 格式化后的输入字典
        """
        # 添加日志记录输入类型和结构
        logger.debug(f"_format_context 接收到输入类型: {type(inputs)}")
        # 获取上下文文档和问题
        context_docs = inputs.get("context", [])
        question = inputs.get("input", "")

        # 确保 context_docs 是列表
        if not isinstance(context_docs, list):
            logger.warning(f"context_docs 不是列表: {context_docs}")
            context_docs = [context_docs] if context_docs else []

        # 格式化上下文信息
        formatted_context = ""
        for i, doc in enumerate(context_docs):
            # 确保 doc 是 LangchainDocument 类型
            if not hasattr(doc, "page_content") or not hasattr(doc, "metadata"):
                logger.warning(f"文档 {i} 不是 LangchainDocument 类型: {doc}")
                continue

            source = doc.metadata.get("source", "未知来源")
            title = doc.metadata.get("title", "无标题")
            similarity = doc.metadata.get("similarity", 0.0)

            formatted_context += f"[文档 {i+1}] (相关度: {similarity:.2f}, 来源: {source}, 标题: {title})\n"
            formatted_context += f"{doc.page_content}\n\n"

        if not formatted_context:
            formatted_context = "没有找到相关的上下文信息。"
            logger.warning(f"查询 '{question}' 没有找到相关上下文")
        else:
            logger.info(f"查询 '{question}' 找到 {len(context_docs)} 个相关文档")

        return {"context": formatted_context, "input": question}

    def invoke(
        self, query: str, doc_ids: Optional[List[int]] = None
    ) -> Tuple[str, List[LangchainDocument]]:
        """执行RAG链

        Args:
            query: 查询文本
            doc_ids: 文档ID列表，如果提供，则只在这些文档中检索

        Returns:
            str: 回答文本
        """
        return (
            self.chain.invoke(query, doc_ids=doc_ids),
            self._format_docs(
                self.get_relevant_documents(query=query, doc_ids=doc_ids)
            ),
        )

    def stream(
        self, query: str, doc_ids: Optional[List[int]] = None
    ) -> Generator[str, None, None]:
        """流式执行RAG链

        Args:
            query: 查询文本
            doc_ids: 文档ID列表，如果提供，则只在这些文档中检索

        Returns:
            Generator[str, None, None]: 回答文本生成器
        """
        config = RunnableConfig({"callbacks": []})
        for chunk in self.chain.stream(query, config=config):
            yield chunk

        yield "[end]"
        rel_docs = self.get_relevant_documents(query=query, doc_ids=doc_ids)
        yield self._format_docs(rel_docs)

    def get_relevant_documents(
        self, query: str, doc_ids: Optional[List[int]] = None
    ) -> List[LangchainDocument]:
        """获取相关文档

        Args:
            query: 查询文本
            doc_ids: 文档ID列表，如果提供，则只在这些文档中检索

        Returns:
            List[LangchainDocument]: 相关文档列表
        """
        return self.retriever.get_relevant_documents(query, doc_ids=doc_ids)

    def _format_doc(self, i: int, doc: LangchainDocument) -> str:
        """格式化文档"""
        return f"[文档 {i + 1}] (相关度: {doc.metadata.get('similarity', 0.0):.2f}, 来源: {doc.metadata.get('source', '未知来源')}, 标题: {doc.metadata.get('title', '无标题')})\n{doc.page_content}\n\n"

    def _format_docs(self, docs: List[LangchainDocument]) -> str:
        """格式化文档"""
        return "\n".join(self._format_doc(i, doc) for i, doc in enumerate(docs))

    def test_chain_components(self, query: str = "测试查询") -> Dict[str, Any]:
        """测试链的各个组件是否正常工作

        Args:
            query: 测试查询文本

        Returns:
            Dict[str, Any]: 测试结果
        """
        results = {}

        try:
            # 测试检索器
            logger.info("测试检索器...")
            docs = self.retriever.get_relevant_documents(query)
            results["retriever"] = {
                "success": True,
                "docs_count": len(docs),
                "first_doc": docs[0].page_content[:100] + "..." if docs else None,
            }
            logger.info(f"检索器测试成功，找到 {len(docs)} 个文档")

            # 测试格式化
            logger.info("测试格式化方法...")
            formatted = self._format_context({"context": docs, "input": query})
            results["format_context"] = {
                "success": True,
                "context_length": len(formatted["context"]),
                "context_preview": (
                    formatted["context"][:100] + "..." if formatted["context"] else None
                ),
            }
            logger.info("格式化方法测试成功")

            # 测试LLM
            logger.info("测试LLM...")
            try:
                llm_result = self.llm.invoke(formatted)
                results["llm"] = {
                    "success": True,
                    "result_preview": llm_result[:100] + "..." if llm_result else None,
                }
                logger.info("LLM测试成功")
            except Exception as e:
                results["llm"] = {"success": False, "error": str(e)}
                logger.error(f"LLM测试失败: {e}")

            # 测试完整链
            logger.info("测试完整链...")
            try:
                chain_result = self.chain.invoke(query)
                results["chain"] = {
                    "success": True,
                    "result_preview": (
                        chain_result[:100] + "..." if chain_result else None
                    ),
                }
                logger.info("完整链测试成功")
            except Exception as e:
                results["chain"] = {"success": False, "error": str(e)}
                logger.error(f"完整链测试失败: {e}")

        except Exception as e:
            logger.error(f"测试过程中出错: {e}")
            results["error"] = str(e)

        return results

    def test_chain_stream_components(self, query: str = "测试查询") -> Dict[str, Any]:
        """测试链的各个组件是否正常工作

        Args:
            query: 测试查询文本

        Returns:
            Dict[str, Any]: 测试结果
        """
        results = {}

        try:
            # 测试检索器
            logger.info("测试检索器...")
            docs = self.retriever.get_relevant_documents(query)
            results["retriever"] = {
                "success": True,
                "docs_count": len(docs),
                "first_doc": docs[0].page_content[:100] + "..." if docs else None,
            }
            logger.info(f"检索器测试成功，找到 {len(docs)} 个文档")

            # 测试格式化
            logger.info("测试格式化方法...")
            formatted = self._format_context({"context": docs, "input": query})
            results["format_context"] = {
                "success": True,
                "context_length": len(formatted["context"]),
                "context_preview": (
                    formatted["context"][:100] + "..." if formatted["context"] else None
                ),
            }
            logger.info("格式化方法测试成功")

            # 测试LLM
            logger.info("测试LLM...")
            try:
                llm_result = ""
                for chunk in self.llm.stream(formatted):
                    llm_result += chunk
                    print(chunk, end="", flush=True)

                results["llm"] = {
                    "success": True,
                    "result_preview": llm_result[:100] + "..." if llm_result else None,
                }
                logger.info("LLM测试成功")
            except Exception as e:
                results["llm"] = {"success": False, "error": str(e)}
                logger.error(f"LLM测试失败: {e}")

            # 测试完整链
            logger.info("测试完整链...")
            try:
                chain_result = ""
                for chunk in self.chain.stream(query):
                    chain_result += chunk
                    print(chunk, end="", flush=True)
                results["chain"] = {
                    "success": True,
                    "result_preview": (
                        chain_result[:100] + "..." if chain_result else None
                    ),
                }
                logger.info("完整链测试成功")
            except Exception as e:
                results["chain"] = {"success": False, "error": str(e)}
                logger.error(f"完整链测试失败: {e}")

        except Exception as e:
            logger.error(f"测试过程中出错: {e}")
            results["error"] = str(e)

        return results
