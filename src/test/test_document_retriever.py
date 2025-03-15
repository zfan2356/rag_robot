import logging
import os
import unittest
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document as LangchainDocument

from src.embd import OllamaEmbedding
from src.rag import DocumentRetriever, DocumentStore

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestDocumentRetriever(unittest.TestCase):
    """测试DocumentRetriever类"""

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
                    model_name="nomic-embed-text:latest", normalize_vectors=True
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

    def test_get_relevant_documents(self):
        """测试检索相关文档功能"""
        # 查询文本
        query = "深度学习和神经网络"

        # 检索相关文档
        results = self.retriever.invoke(query)

        # 验证结果
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), self.retriever.top_k)

        # 将结果写入output.txt文件
        output_file_path = os.path.join(os.path.dirname(__file__), "output.txt")
        try:
            import json

            results_json = []
            for doc in results:
                results_json.append(
                    {
                        "page_content": doc.page_content,
                        "metadata": {
                            "similarity": doc.metadata["similarity"],
                            "doc_id": doc.metadata["doc_id"],
                            "title": doc.metadata["title"],
                        },
                    }
                )

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(results_json, ensure_ascii=False, indent=2))
            logger.info(f"检索结果已写入文件: {output_file_path}")
        except Exception as e:
            logger.error(f"写入结果到文件时出错: {str(e)}")

        # 验证结果格式
        for doc in results:
            self.assertIsInstance(doc, LangchainDocument)
            self.assertIsNotNone(doc.page_content)
            self.assertIn("similarity", doc.metadata)
            self.assertIn("doc_id", doc.metadata)
            self.assertIn("title", doc.metadata)

            # 验证相似度
            similarity = doc.metadata["similarity"]
            self.assertGreaterEqual(similarity, self.retriever.similarity_threshold)
            self.assertLessEqual(similarity, 1.0)

        # 验证结果排序
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i].metadata["similarity"], results[i + 1].metadata["similarity"]
            )

        # 验证最相关的文档应该包含查询关键词
        if results:
            found = False
            for keyword in ["深度学习", "神经网络"]:
                if keyword in results[0].page_content:
                    found = True
                    break

            self.assertTrue(found, f"最相关的文档应该包含查询关键词")

        logger.info(f"检索相关文档成功，查询: '{query}'，找到 {len(results)} 个结果")
        if results:
            logger.info(f"最相关文档相似度: {results[0].metadata['similarity']:.4f}")
            logger.info(f"最相关文档标题: {results[0].metadata['title']}")

    def test_get_relevant_documents_with_doc_ids(self):
        """测试在指定文档中检索相关文档功能"""
        # 查询文本
        query = "人工智能应用"

        # 指定文档ID
        doc_ids = self.test_doc_ids[:2]  # 只在前两个文档中检索

        # 检索相关文档
        results = self.retriever.invoke(query, doc_ids=doc_ids)

        # 验证结果
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)

        # 验证结果只来自指定的文档
        for doc in results:
            self.assertIn(doc.metadata["doc_id"], doc_ids)

        logger.info(
            f"在指定文档中检索成功，查询: '{query}'，找到 {len(results)} 个结果"
        )

    def test_clear_and_update_cache(self):
        """测试清除和更新缓存功能"""
        # 初始状态应该有缓存
        self.assertIsNotNone(self.retriever._document_chunks)
        self.assertTrue(hasattr(self.retriever, "_chunk_embeddings"))

        # 清除缓存
        self.retriever.clear_cache()

        # 验证缓存已清除
        self.assertIsNone(self.retriever._document_chunks)
        self.assertFalse(hasattr(self.retriever, "_chunk_embeddings"))

        # 更新缓存
        self.retriever.update_cache()

        # 验证缓存已更新
        self.assertIsNotNone(self.retriever._document_chunks)
        self.assertTrue(hasattr(self.retriever, "_chunk_embeddings"))

        # 验证缓存内容
        self.assertGreater(len(self.retriever._document_chunks), 0)
        self.assertEqual(
            len(self.retriever._document_chunks), len(self.retriever._chunk_embeddings)
        )

        logger.info(
            f"缓存清除和更新成功，缓存了 {len(self.retriever._document_chunks)} 个文档块"
        )

    def test_similarity_threshold_filtering(self):
        """测试相似度阈值过滤功能"""
        # 创建一个高阈值的检索器
        high_threshold_retriever = DocumentRetriever(
            document_store=self.doc_store,
            embedding_model=self.embedding_model,
            top_k=10,
            similarity_threshold=0.9,  # 设置一个很高的阈值
        )

        # 更新缓存
        high_threshold_retriever.update_cache()

        # 查询文本
        query = "量子计算和区块链技术"  # 一个与测试文档关联度较低的查询

        # 检索相关文档
        results = high_threshold_retriever.invoke(query)

        # 验证结果
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)

        # 由于阈值很高，可能没有结果
        if not results:
            logger.info(f"高阈值检索没有找到结果，符合预期")
        else:
            # 如果有结果，验证所有结果的相似度都高于阈值
            for doc in results:
                self.assertGreaterEqual(
                    doc.metadata["similarity"],
                    high_threshold_retriever.similarity_threshold,
                )

            logger.info(
                f"高阈值检索找到 {len(results)} 个结果，最高相似度: {results[0].metadata['similarity']:.4f}"
            )


if __name__ == "__main__":
    unittest.main()
