import logging
import os
import unittest
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document as LangchainDocument

from src.embd import OllamaEmbedding
from src.rag import DocumentStore

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestDocumentStore(unittest.TestCase):
    """测试DocumentStore类"""

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
                    model_name="nomic-embed-text",  # 移除:latest，使用默认版本
                    normalize_vectors=True,
                )
                logger.info("成功创建嵌入模型")
            except Exception as e:
                logger.error(f"创建嵌入模型时出错: {str(e)}")
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
            ]

            # 记录测试文档ID
            cls.test_doc_ids = []

            logger.info(f"测试环境设置完成，使用数据库: {cls.test_db_url}")

        except Exception as e:
            logger.error(f"设置测试环境时出错: {str(e)}")
            raise unittest.SkipTest(f"设置测试环境失败: {str(e)}")

    def setUp(self):
        """每个测试前的准备工作"""
        # 清空之前的测试文档ID
        self.__class__.test_doc_ids = []

    def tearDown(self):
        """每个测试后的清理工作"""
        # 删除测试过程中创建的文档
        for doc_id in self.__class__.test_doc_ids:
            try:
                self.doc_store.delete_document(doc_id)
                logger.info(f"已删除测试文档，ID: {doc_id}")
            except Exception as e:
                logger.warning(f"删除测试文档 {doc_id} 时出错: {str(e)}")

    def test_add_document(self):
        """测试添加文档功能"""
        # 添加测试文档
        doc = self.test_docs[0]
        doc_id = self.doc_store.add_document(content=doc["content"], title=doc["title"])

        # 记录文档ID以便清理
        self.__class__.test_doc_ids.append(doc_id)

        # 验证文档ID是否有效
        self.assertIsNotNone(doc_id)
        self.assertGreater(doc_id, 0)

        logger.info(f"文档添加成功，ID: {doc_id}")

    def test_get_document(self):
        """测试获取文档功能"""
        # 添加测试文档
        doc = self.test_docs[1]
        doc_id = self.doc_store.add_document(content=doc["content"], title=doc["title"])

        # 记录文档ID以便清理
        self.__class__.test_doc_ids.append(doc_id)

        # 获取文档
        retrieved_doc = self.doc_store.get_document(doc_id)

        # 验证文档内容
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc["doc"], doc["content"])
        self.assertEqual(retrieved_doc["title"], doc["title"])

        logger.info(f"文档获取成功，ID: {doc_id}, 标题: {retrieved_doc['title']}")

    def test_delete_document(self):
        """测试删除文档功能"""
        # 添加测试文档
        doc = self.test_docs[2]
        doc_id = self.doc_store.add_document(content=doc["content"], title=doc["title"])

        # 验证文档已添加
        self.assertIsNotNone(self.doc_store.get_document(doc_id))

        # 删除文档
        result = self.doc_store.delete_document(doc_id)

        # 验证删除结果
        self.assertTrue(result)

        # 验证文档已删除
        self.assertIsNone(self.doc_store.get_document(doc_id))

        logger.info(f"文档删除成功，ID: {doc_id}")

    def test_list_documents(self):
        """测试列出所有文档功能"""
        # 添加多个测试文档
        doc_ids = []
        for doc in self.test_docs:
            doc_id = self.doc_store.add_document(
                content=doc["content"], title=doc["title"]
            )
            doc_ids.append(doc_id)

        # 记录文档ID以便清理
        self.__class__.test_doc_ids.extend(doc_ids)

        # 列出所有文档
        docs = self.doc_store.list_documents()

        # 验证文档列表
        self.assertIsNotNone(docs)
        self.assertIsInstance(docs, list)

        # 验证所有添加的文档都在列表中
        doc_ids_in_list = [doc["id"] for doc in docs]
        for doc_id in doc_ids:
            self.assertIn(doc_id, doc_ids_in_list)

        logger.info(f"列出文档成功，共 {len(docs)} 个文档")

    def test_search_documents(self):
        """测试搜索文档功能"""
        # 添加多个测试文档
        doc_ids = []
        for doc in self.test_docs:
            doc_id = self.doc_store.add_document(
                content=doc["content"], title=doc["title"]
            )
            doc_ids.append(doc_id)

        # 记录文档ID以便清理
        self.__class__.test_doc_ids.extend(doc_ids)

        # 搜索文档
        keyword = "深度学习"
        results = self.doc_store.search_documents(keyword)

        # 验证搜索结果
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)

        # 验证搜索结果包含关键词
        found = False
        for doc in results:
            if keyword in doc.get("doc_preview", ""):
                found = True
                break

        self.assertTrue(found, f"搜索结果中应该包含关键词 '{keyword}'")

        logger.info(f"搜索文档成功，关键词 '{keyword}'，找到 {len(results)} 个结果")

    def test_get_document_chunks(self):
        """测试获取文档分块功能"""
        # 添加一个较长的测试文档
        long_doc = {
            "content": "人工智能（Artificial Intelligence，简称AI）是研究如何使计算机模拟人类智能的一门学科。"
            "它包括机器学习、深度学习、自然语言处理、计算机视觉等多个分支。"
            "随着技术的发展，AI已经在医疗、金融、教育等多个领域得到了广泛应用。\n\n"
            "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习。"
            "常见的机器学习算法包括监督学习、无监督学习和强化学习。"
            "监督学习需要标记的训练数据，无监督学习不需要标记，而强化学习通过奖励机制来学习。\n\n"
            "深度学习是机器学习的一种方法，使用神经网络进行学习。"
            "神经网络由多层神经元组成，可以自动提取特征并进行复杂的模式识别。"
            "深度学习在图像识别、语音识别和自然语言处理等任务上取得了突破性进展。\n\n"
            "自然语言处理（NLP）是人工智能的一个分支，研究计算机与人类语言的交互。"
            "NLP技术包括文本分类、情感分析、命名实体识别、机器翻译等。"
            "近年来，基于Transformer架构的模型如BERT、GPT等在NLP领域取得了显著成果。\n\n"
            "计算机视觉是人工智能的另一个重要分支，研究如何让计算机理解图像和视频。"
            "计算机视觉技术包括图像分类、目标检测、图像分割、人脸识别等。"
            "卷积神经网络（CNN）是计算机视觉中最常用的深度学习模型之一。",
            "title": "人工智能综合介绍",
        }

        doc_id = self.doc_store.add_document(
            content=long_doc["content"], title=long_doc["title"]
        )

        # 记录文档ID以便清理
        self.__class__.test_doc_ids.append(doc_id)

        # 获取文档分块
        chunks = self.doc_store.get_document_chunks(doc_id)

        # 验证分块结果
        self.assertIsNotNone(chunks)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 1, "长文档应该被分成多个块")

        # 验证分块内容
        for chunk in chunks:
            self.assertIsInstance(chunk, LangchainDocument)
            self.assertIsNotNone(chunk.page_content)
            self.assertGreater(len(chunk.page_content), 0)

            # 验证元数据
            self.assertEqual(chunk.metadata["doc_id"], doc_id)
            self.assertEqual(chunk.metadata["title"], long_doc["title"])
            self.assertIn("chunk_id", chunk.metadata)
            self.assertIn("source", chunk.metadata)

        logger.info(f"文档分块成功，ID: {doc_id}，共 {len(chunks)} 个块")

    def test_get_all_document_chunks(self):
        """测试获取所有文档分块功能"""
        # 添加多个测试文档
        doc_ids = []
        for doc in self.test_docs:
            doc_id = self.doc_store.add_document(
                content=doc["content"], title=doc["title"]
            )
            doc_ids.append(doc_id)

        # 记录文档ID以便清理
        self.__class__.test_doc_ids.extend(doc_ids)

        # 获取所有文档分块
        all_chunks = self.doc_store.get_all_document_chunks()

        # 验证分块结果
        self.assertIsNotNone(all_chunks)
        self.assertIsInstance(all_chunks, list)

        # 验证所有文档的分块都在结果中
        doc_ids_in_chunks = set()
        for chunk in all_chunks:
            doc_ids_in_chunks.add(chunk.metadata["doc_id"])

        for doc_id in doc_ids:
            self.assertIn(doc_id, doc_ids_in_chunks)

        logger.info(
            f"获取所有文档分块成功，共 {len(all_chunks)} 个块，涉及 {len(doc_ids_in_chunks)} 个文档"
        )
