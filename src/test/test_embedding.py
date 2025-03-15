import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from src.embd import (
    EmbeddingModel,
    OllamaEmbedding,
    cosine_similarity,
    search_similar_texts,
)


class MockEmbeddingModel(EmbeddingModel):
    """用于测试的模拟嵌入模型"""

    def get_embeddings(self, texts):
        """返回模拟的嵌入向量"""
        # 为每个文本生成一个随机向量，但确保相似的文本有相似的向量
        embeddings = []
        for text in texts:
            if "人工智能" in text:
                # 人工智能相关的文本向量相似
                base = np.array([0.1, 0.2, 0.3])
                noise = np.random.normal(0, 0.05, 3)
                vec = base + noise
            elif "机器学习" in text:
                # 机器学习相关的文本向量相似
                base = np.array([0.2, 0.3, 0.4])
                noise = np.random.normal(0, 0.05, 3)
                vec = base + noise
            elif "深度学习" in text or "神经网络" in text:
                # 深度学习相关的文本向量相似
                base = np.array([0.3, 0.4, 0.5])
                noise = np.random.normal(0, 0.05, 3)
                vec = base + noise
            else:
                # 其他文本随机向量
                vec = np.random.rand(3)

            # 归一化向量
            vec = vec / np.linalg.norm(vec)
            embeddings.append(vec.tolist())

        return embeddings


class TestEmbedding(unittest.TestCase):
    """测试嵌入功能"""

    def setUp(self):
        """测试前的准备工作"""
        self.mock_model = MockEmbeddingModel()
        self.test_texts = [
            "人工智能是研究如何使计算机模拟人类智能的一门学科",
            "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习",
            "深度学习是机器学习的一种方法，使用神经网络进行学习",
            "自然语言处理是人工智能的一个分支，研究计算机与人类语言的交互",
            "计算机视觉是人工智能的一个领域，研究如何让计算机理解图像和视频",
        ]

    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]  # 相同向量
        vec3 = [0, 1, 0]  # 正交向量
        vec4 = [-1, 0, 0]  # 相反向量

        # 相同向量的相似度应为1
        self.assertAlmostEqual(cosine_similarity(vec1, vec2), 1.0)

        # 正交向量的相似度应为0
        self.assertAlmostEqual(cosine_similarity(vec1, vec3), 0.0)

        # 相反向量的相似度应为-1
        self.assertAlmostEqual(cosine_similarity(vec1, vec4), -1.0)

    def test_search_similar_texts(self):
        """测试相似文本搜索"""
        query = "深度学习和神经网络"
        results = search_similar_texts(query, self.test_texts, self.mock_model, top_k=3)

        # 验证结果格式
        self.assertEqual(len(results), 3)
        self.assertIn("text", results[0])
        self.assertIn("similarity", results[0])

        # 验证结果排序
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i]["similarity"], results[i + 1]["similarity"]
            )

        # 验证相似度范围
        for result in results:
            self.assertGreaterEqual(result["similarity"], -1.0)
            self.assertLessEqual(result["similarity"], 1.0)

    @patch("requests.post")
    @patch("requests.get")
    def test_ollama_embedding_init(self, mock_get, mock_post):
        """测试OllamaEmbedding初始化"""
        # 模拟Ollama服务响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "nomic-embed-text:latest"}]
        }
        mock_get.return_value = mock_response

        # 初始化OllamaEmbedding
        embedding = OllamaEmbedding()

        # 验证初始化参数
        self.assertEqual(embedding.base_url, "http://localhost:11434")
        self.assertEqual(embedding.model_name, "nomic-embed-text:latest")
        self.assertEqual(embedding.api_url, "http://localhost:11434/api/embeddings")

        # 验证检查可用性方法被调用
        mock_get.assert_called_once_with("http://localhost:11434/api/tags")

    @patch("requests.post")
    @patch("requests.get")
    def test_ollama_get_embeddings(self, mock_get, mock_post):
        """测试OllamaEmbedding.get_embeddings方法"""
        # 模拟Ollama服务响应
        get_response = MagicMock()
        get_response.status_code = 200
        get_response.json.return_value = {
            "models": [{"name": "nomic-embed-text:latest"}]
        }
        mock_get.return_value = get_response

        # 模拟嵌入向量响应
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_post.return_value = post_response

        # 初始化OllamaEmbedding并获取嵌入向量
        embedding = OllamaEmbedding()
        texts = ["测试文本"]
        embeddings = embedding.get_embeddings(texts)

        # 验证结果
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])

        # 验证API调用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:11434/api/embeddings")
        self.assertEqual(kwargs["json"]["model"], "nomic-embed-text:latest")
        self.assertEqual(kwargs["json"]["prompt"], "测试文本")

    @patch("requests.post")
    @patch("requests.get")
    def test_ollama_error_handling(self, mock_get, mock_post):
        """测试OllamaEmbedding错误处理"""
        # 模拟Ollama服务响应
        get_response = MagicMock()
        get_response.status_code = 200
        get_response.json.return_value = {
            "models": [{"name": "nomic-embed-text:latest"}]
        }
        mock_get.return_value = get_response

        # 模拟错误响应
        post_response = MagicMock()
        post_response.status_code = 500
        post_response.text = "Internal Server Error"
        mock_post.return_value = post_response

        # 初始化OllamaEmbedding并获取嵌入向量
        embedding = OllamaEmbedding()
        texts = ["测试文本"]
        embeddings = embedding.get_embeddings(texts)

        # 验证结果 - 应该返回零向量
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(len(embeddings[0]), 768)
        self.assertEqual(sum(embeddings[0]), 0.0)
