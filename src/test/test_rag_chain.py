import logging
import os
import unittest
from typing import Any, Dict, List, Optional

from src.embd import OllamaEmbedding
from src.llm import LocalBaseLLM
from src.rag import DocumentRetriever, DocumentStore, RagChain

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRagChain(unittest.TestCase):
    """测试RagChain类"""

    @classmethod
    def setUpClass(cls):
        """在所有测试之前设置测试环境"""
        try:
            # 使用测试数据库URL
            cls.test_db_url = os.environ.get(
                "TEST_DB_URL", "mysql+pymysql://root:123456@localhost/rag_robot"
            )

            logger.info(f"使用数据库URL: {cls.test_db_url}")

            # 创建嵌入模型
            try:
                cls.embedding_model = OllamaEmbedding(
                    model_name="nomic-embed-text:latest",  # 使用默认版本
                    normalize_vectors=True,
                )
                logger.info("成功创建嵌入模型")
            except Exception as e:
                logger.error(f"创建嵌入模型时出错: {str(e)}")
                raise

            # 创建LLM
            try:
                cls.llm = LocalBaseLLM(model_name="llama3.2:latest")
                logger.info("成功创建LLM")
            except Exception as e:
                logger.error(f"创建LLM时出错: {str(e)}")
                raise

            # 创建DocumentStore实例
            try:
                cls.doc_store = DocumentStore(
                    embedding_model=cls.embedding_model,
                    db_url=cls.test_db_url,
                    chunk_size=500,  # 使用较小的块大小以便测试
                    chunk_overlap=100,
                )
                logger.info("成功创建DocumentStore实例")
            except Exception as e:
                logger.error(f"创建DocumentStore实例时出错: {str(e)}")
                raise

            # 创建DocumentRetriever实例
            try:
                cls.retriever = DocumentRetriever(
                    document_store=cls.doc_store,
                    embedding_model=cls.embedding_model,
                    top_k=3,
                    similarity_threshold=0.5,
                )
                logger.info("成功创建DocumentRetriever实例")
            except Exception as e:
                logger.error(f"创建DocumentRetriever实例时出错: {str(e)}")
                raise

            # 创建RagChain实例
            try:
                cls.rag_chain = RagChain(
                    retriever=cls.retriever,
                )
                logger.info("成功创建RagChain实例")
            except Exception as e:
                logger.error(f"创建RagChain实例时出错: {str(e)}")
                raise

            # 测试文档
            cls.test_docs = [
                {
                    "content": "人工智能（Artificial Intelligence，简称AI）是研究如何使计算机模拟人类智能的一门学科。"
                    "它包括机器学习、深度学习、自然语言处理、计算机视觉等多个分支。"
                    "随着技术的发展，AI已经在医疗、金融、教育等多个领域得到了广泛应用。",
                    "title": "人工智能简介",
                },
                {
                    "content": "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习。"
                    "常见的机器学习算法包括监督学习、无监督学习和强化学习。"
                    "监督学习需要标记的训练数据，无监督学习不需要标记，而强化学习通过奖励机制来学习。",
                    "title": "机器学习概述",
                },
                {
                    "content": "深度学习是机器学习的一种方法，使用神经网络进行学习。"
                    "神经网络由多层神经元组成，可以自动提取特征并进行复杂的模式识别。"
                    "深度学习在图像识别、语音识别和自然语言处理等任务上取得了突破性进展。",
                    "title": "深度学习入门",
                },
                {
                    "content": "自然语言处理（NLP）是人工智能的一个分支，研究计算机与人类语言的交互。"
                    "NLP技术包括文本分类、情感分析、命名实体识别、机器翻译等。"
                    "近年来，基于Transformer架构的模型如BERT、GPT等在NLP领域取得了显著成果。",
                    "title": "自然语言处理概述",
                },
                {
                    "content": "计算机视觉是人工智能的另一个重要分支，研究如何让计算机理解图像和视频。"
                    "计算机视觉技术包括图像分类、目标检测、图像分割、人脸识别等。"
                    "卷积神经网络（CNN）是计算机视觉中最常用的深度学习模型之一。",
                    "title": "计算机视觉技术",
                },
            ]

            # 记录测试文档ID
            cls.test_doc_ids = []

            # 添加测试文档
            try:
                for doc in cls.test_docs:
                    doc_id = cls.doc_store.add_document(
                        content=doc["content"], title=doc["title"]
                    )
                    cls.test_doc_ids.append(doc_id)
                logger.info(f"成功添加 {len(cls.test_doc_ids)} 个测试文档")
            except Exception as e:
                logger.error(f"添加测试文档时出错: {str(e)}")
                raise

            # 更新检索器缓存
            try:
                cls.retriever.update_cache()
                logger.info("成功更新检索器缓存")
            except Exception as e:
                logger.error(f"更新检索器缓存时出错: {str(e)}")
                raise

            logger.info(f"测试环境设置完成，使用数据库: {cls.test_db_url}")
            logger.info(f"已添加 {len(cls.test_doc_ids)} 个测试文档")

        except Exception as e:
            logger.error(f"设置测试环境时出错: {str(e)}")
            raise unittest.SkipTest(f"设置测试环境失败: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """在所有测试后的清理工作"""
        # 删除测试过程中创建的文档
        for doc_id in cls.test_doc_ids:
            try:
                cls.doc_store.delete_document(doc_id)
                logger.info(f"已删除测试文档，ID: {doc_id}")
            except Exception as e:
                logger.warning(f"删除测试文档 {doc_id} 时出错: {str(e)}")

    def test_pass(self):
        result = self.rag_chain.test_chain_components(
            "什么是深度学习？它与机器学习有什么关系？"
        )
        logger.info(f"test_chain_components result: {result}")

    def test_invoke(self):
        """测试执行RAG链功能"""
        # 查询文本
        query = "什么是深度学习？它与机器学习有什么关系？"

        # 执行RAG链
        response = self.rag_chain.invoke(query)

        # 验证结果
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

        logger.info(f"RAG链执行成功，查询: '{query}'")
        logger.info(f"回答: {response[:100]}...")  # 只显示前100个字符

    def test_invoke_with_doc_ids(self):
        """测试在指定文档中执行RAG链功能"""
        # 查询文本
        query = "什么是自然语言处理？"

        # 指定文档ID
        doc_ids = [self.test_doc_ids[3]]  # 只使用自然语言处理的文档

        # 执行RAG链
        response = self.rag_chain.invoke(query, doc_ids=doc_ids)

        # 验证结果
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

        logger.info(f"在指定文档中执行RAG链成功，查询: '{query}'")
        logger.info(f"回答: {response[:100]}...")  # 只显示前100个字符

    def test_stream(self):
        """测试流式执行RAG链功能"""
        # 查询文本
        query = "计算机视觉有哪些应用？"

        # 流式执行RAG链
        response_chunks = []
        for chunk in self.rag_chain.stream(query):
            response_chunks.append(chunk)

        # 验证结果
        self.assertGreater(len(response_chunks), 0)

        # 合并所有块
        full_response = "".join(response_chunks)
        self.assertGreater(len(full_response), 0)

        logger.info(f"RAG链流式执行成功，查询: '{query}'")
        logger.info(f"收到 {len(response_chunks)} 个响应块")
        logger.info(f"完整回答: {full_response[:100]}...")  # 只显示前100个字符

    def test_update_system_prompt(self):
        """测试更新系统提示词功能"""
        # 原始系统提示词
        original_prompt = self.rag_chain.system_prompt

        # 新的系统提示词
        new_prompt = """
        你是一个专业的AI研究员，请根据提供的上下文信息回答用户的问题。
        回答应该专业、准确，并引用上下文中的相关信息。
        如果上下文信息不足以回答问题，请明确指出并建议用户提供更多信息。
        """

        # 更新系统提示词
        self.rag_chain.update_system_prompt(new_prompt)

        # 验证系统提示词已更新
        self.assertEqual(self.rag_chain.system_prompt, new_prompt)

        # 查询文本
        query = "简要介绍一下机器学习"

        # 执行RAG链
        response = self.rag_chain.invoke(query)

        # 验证结果
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

        logger.info(f"系统提示词更新成功")
        logger.info(f"使用新提示词的回答: {response[:100]}...")  # 只显示前100个字符

        # 恢复原始系统提示词
        self.rag_chain.update_system_prompt(original_prompt)

    def test_get_relevant_documents(self):
        """测试获取相关文档功能"""
        # 查询文本
        query = "深度学习和神经网络"

        # 获取相关文档
        results = self.rag_chain.get_relevant_documents(query)

        # 验证结果
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), self.retriever.top_k)

        # 验证最相关的文档应该包含查询关键词
        if results:
            found = False
            for keyword in ["深度学习", "神经网络"]:
                if keyword in results[0].page_content:
                    found = True
                    break

            self.assertTrue(found, f"最相关的文档应该包含查询关键词")

        logger.info(f"获取相关文档成功，查询: '{query}'，找到 {len(results)} 个结果")


if __name__ == "__main__":
    unittest.main()
