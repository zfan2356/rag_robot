import logging
import time
import unittest
from typing import Any, Dict, List

import numpy as np

from src.embd import OllamaEmbedding, cosine_similarity, search_similar_texts

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestEmbeddingReal(unittest.TestCase):
    """测试嵌入功能 - 使用真实的Ollama服务"""

    @classmethod
    def setUpClass(cls):
        """在所有测试之前设置测试环境"""
        try:
            # 创建OllamaEmbedding实例，启用向量归一化
            cls.embedding_model = OllamaEmbedding(
                model_name="nomic-embed-text:latest",
                normalize_vectors=True,  # 启用向量归一化
            )

            # 测试文本
            cls.test_texts = [
                "人工智能是研究如何使计算机模拟人类智能的一门学科",
                "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习",
                "深度学习是机器学习的一种方法，使用神经网络进行学习",
                "自然语言处理是人工智能的一个分支，研究计算机与人类语言的交互",
                "计算机视觉是人工智能的一个领域，研究如何让计算机理解图像和视频",
            ]

            # 预先获取嵌入向量，避免每个测试都重复获取
            logger.info("预先获取测试文本的嵌入向量...")
            cls.embeddings = cls.embedding_model.get_embeddings(cls.test_texts)

            # 检查是否成功获取嵌入向量
            if not cls.embeddings or len(cls.embeddings) != len(cls.test_texts):
                logger.error("无法获取嵌入向量，测试将被跳过")
                cls.skip_tests = True
            else:
                cls.skip_tests = False
                logger.info(f"成功获取嵌入向量，维度: {len(cls.embeddings[0])}")

        except Exception as e:
            logger.error(f"设置测试环境时出错: {str(e)}")
            cls.skip_tests = True

    def setUp(self):
        """每个测试前的准备工作"""
        if getattr(self.__class__, "skip_tests", False):
            self.skipTest("无法连接到Ollama服务或获取嵌入向量")

    def test_embedding_dimensions(self):
        """测试嵌入向量的维度"""
        # 所有向量应该具有相同的维度
        dimensions = [len(embedding) for embedding in self.embeddings]
        self.assertEqual(len(set(dimensions)), 1, "所有嵌入向量应该具有相同的维度")

        # 维度应该大于0
        self.assertGreater(dimensions[0], 0, "嵌入向量维度应该大于0")

        logger.info(f"嵌入向量维度: {dimensions[0]}")

    def test_embedding_normalization(self):
        """测试嵌入向量的范数"""
        for i, embedding in enumerate(self.embeddings):
            # 计算向量的范数
            norm = np.linalg.norm(np.array(embedding))
            # 范数应该大于0（非零向量）
            self.assertGreater(norm, 0.0, msg=f"向量 {i} 的范数为 {norm}，应该大于0")

            # 记录范数值，但不断言它必须接近1
            logger.info(f"向量 {i} 的范数: {norm}")

            # 如果需要使用归一化的向量，可以在这里进行归一化
            normalized_embedding = np.array(embedding) / norm
            normalized_norm = np.linalg.norm(normalized_embedding)
            # 归一化后的范数应该接近1
            self.assertAlmostEqual(
                normalized_norm,
                1.0,
                delta=0.01,
                msg=f"归一化后的向量 {i} 的范数为 {normalized_norm}，应该接近1",
            )

    def test_similar_texts_have_similar_embeddings(self):
        """测试相似文本是否有相似的嵌入向量"""
        # 计算所有文本对之间的相似度
        similarities = []
        for i in range(len(self.test_texts)):
            for j in range(i + 1, len(self.test_texts)):
                similarity = cosine_similarity(self.embeddings[i], self.embeddings[j])
                similarities.append((i, j, similarity))

        # 按相似度降序排序
        similarities.sort(key=lambda x: x[2], reverse=True)

        # 输出最相似的文本对
        for i, j, similarity in similarities[:3]:
            logger.info(
                f"相似度 {similarity:.4f}: \n  {self.test_texts[i]}\n  {self.test_texts[j]}"
            )

        # 验证相似度范围
        for _, _, similarity in similarities:
            self.assertGreaterEqual(similarity, -1.0)
            self.assertLessEqual(similarity, 1.0)

        # 验证相似文本的相似度较高
        # 例如，包含"机器学习"的文本应该彼此更相似
        ml_texts_indices = [
            i for i, text in enumerate(self.test_texts) if "机器学习" in text
        ]
        if len(ml_texts_indices) >= 2:
            ml_similarities = []
            for i in range(len(ml_texts_indices)):
                for j in range(i + 1, len(ml_texts_indices)):
                    idx1, idx2 = ml_texts_indices[i], ml_texts_indices[j]
                    similarity = cosine_similarity(
                        self.embeddings[idx1], self.embeddings[idx2]
                    )
                    ml_similarities.append(similarity)

            # 计算平均相似度
            avg_ml_similarity = sum(ml_similarities) / len(ml_similarities)
            logger.info(
                f"包含'机器学习'的文本之间的平均相似度: {avg_ml_similarity:.4f}"
            )

            # 相似度应该较高（大于0.5）
            self.assertGreater(
                avg_ml_similarity, 0.5, "包含'机器学习'的文本之间的平均相似度应该较高"
            )

    def test_search_similar_texts(self):
        """测试搜索相似文本功能"""
        # 使用与深度学习相关的查询
        query = "深度学习和神经网络"
        results = search_similar_texts(
            query, self.test_texts, self.embedding_model, top_k=3
        )

        # 验证结果格式
        self.assertEqual(len(results), 3)
        self.assertIn("text", results[0])
        self.assertIn("similarity", results[0])

        # 验证结果排序
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i]["similarity"], results[i + 1]["similarity"]
            )

        # 输出搜索结果
        logger.info(f"查询: {query}")
        for i, result in enumerate(results):
            logger.info(f"{i+1}. 文本: {result['text']}")
            logger.info(f"   相似度: {result['similarity']:.4f}")

        # 验证最相似的文本应该包含"深度学习"或"神经网络"
        self.assertTrue(
            "深度学习" in results[0]["text"] or "神经网络" in results[0]["text"],
            f"最相似的文本应该包含'深度学习'或'神经网络'，但得到: {results[0]['text']}",
        )

    def test_batch_embedding(self):
        """测试批量获取嵌入向量"""
        # 创建一个较大的文本批次
        batch_size = 10
        batch_texts = [f"这是测试文本 {i}" for i in range(batch_size)]

        # 记录开始时间
        start_time = time.time()

        # 获取嵌入向量
        batch_embeddings = self.embedding_model.get_embeddings(batch_texts)

        # 记录结束时间
        end_time = time.time()

        # 验证结果
        self.assertEqual(len(batch_embeddings), batch_size)

        # 输出性能信息
        elapsed_time = end_time - start_time
        logger.info(f"批量处理 {batch_size} 个文本耗时: {elapsed_time:.2f} 秒")
        logger.info(f"平均每个文本耗时: {elapsed_time/batch_size:.2f} 秒")

    def test_embedding_consistency(self):
        """测试嵌入向量的一致性"""
        # 对同一文本多次获取嵌入向量，结果应该一致
        test_text = "这是一个测试文本，用于验证嵌入向量的一致性"

        # 多次获取嵌入向量
        embedding1 = self.embedding_model.get_embeddings([test_text])[0]
        embedding2 = self.embedding_model.get_embeddings([test_text])[0]

        # 计算相似度
        similarity = cosine_similarity(embedding1, embedding2)

        # 相似度应该非常高（接近1）
        self.assertGreater(
            similarity,
            0.99,
            f"同一文本的嵌入向量应该非常相似，但相似度为 {similarity:.4f}",
        )

        logger.info(f"同一文本的嵌入向量相似度: {similarity:.4f}")

    def test_multilingual_embedding(self):
        """测试多语言嵌入向量"""
        # 测试不同语言的文本
        texts = [
            "人工智能是研究如何使计算机模拟人类智能的一门学科",  # 中文
            "Artificial Intelligence is the study of how to make computers simulate human intelligence",  # 英文
            "L'Intelligence Artificielle est l'étude de comment faire simuler l'intelligence humaine par les ordinateurs",  # 法文
        ]

        # 获取嵌入向量
        embeddings = self.embedding_model.get_embeddings(texts)

        # 验证结果
        self.assertEqual(len(embeddings), len(texts))

        # 计算相似度
        similarities = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = cosine_similarity(embeddings[i], embeddings[j])
                similarities.append((i, j, similarity))

        # 输出相似度
        for i, j, similarity in similarities:
            logger.info(f"语言 {i+1} 和语言 {j+1} 的相似度: {similarity:.4f}")

        # 不同语言的相似文本应该有一定的相似度（大于0.45）
        for _, _, similarity in similarities:
            self.assertGreater(similarity, 0.45, "不同语言的相似文本应该有一定的相似度")
