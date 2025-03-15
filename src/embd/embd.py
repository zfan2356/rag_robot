import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import numpy as np
import requests
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmbeddingModel:
    """嵌入模型基类"""

    def __init__(self):
        pass

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本嵌入向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        raise NotImplementedError("子类必须实现此方法")


class OllamaEmbedding(EmbeddingModel):
    """使用Ollama的嵌入模型"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "nomic-embed-text",
        normalize_vectors: bool = False,
    ):
        """初始化Ollama嵌入模型

        Args:
            base_url: Ollama服务的基础URL
            model_name: 嵌入模型名称，默认为nomic-embed-text
            normalize_vectors: 是否归一化嵌入向量，默认为False
        """
        super().__init__()
        self.base_url = base_url
        self.model_name = model_name
        self.api_url = f"{base_url}/api/embeddings"
        self.normalize_vectors = normalize_vectors

        # 检查Ollama服务是否可用
        self._check_availability()

    def _check_availability(self) -> bool:
        """检查Ollama服务是否可用

        Returns:
            bool: 服务是否可用
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]

                if self.model_name not in available_models:
                    logger.warning(
                        f"模型 {self.model_name} 不在可用模型列表中，可能需要先拉取"
                    )
                    logger.info(
                        f"可用模型: {available_models}, 使用默认模型nomic-embed-text:latest "
                    )
                    self.model_name = "nomic-embed-text:latest"

                logger.info(f"Ollama服务可用，使用模型: {self.model_name}")
                return True
            else:
                logger.warning(f"Ollama服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"检查Ollama服务时出错: {str(e)}")
            return False

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本嵌入向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        embeddings = []

        for text in tqdm(texts, desc="获取嵌入向量"):
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": text,
                    "options": {"temperature": 0.0},
                }

                response = requests.post(self.api_url, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", [])

                    # 如果需要归一化向量
                    if self.normalize_vectors and embedding:
                        embedding_array = np.array(embedding)
                        norm = np.linalg.norm(embedding_array)
                        if norm > 0:
                            embedding = (embedding_array / norm).tolist()

                    embeddings.append(embedding)
                else:
                    logger.error(
                        f"获取嵌入向量失败: {response.status_code} - {response.text}"
                    )
                    # 返回零向量作为回退
                    embeddings.append([0.0] * 768)  # 假设维度为768
            except Exception as e:
                logger.error(f"获取嵌入向量时出错: {str(e)}")
                # 返回零向量作为回退
                embeddings.append([0.0] * 768)  # 假设维度为768

        return embeddings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度

    Args:
        vec1: 向量1
        vec2: 向量2

    Returns:
        float: 余弦相似度
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    # 确保向量已归一化
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)

    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0

    # 归一化向量
    vec1 = vec1 / norm_vec1
    vec2 = vec2 / norm_vec2

    # 计算归一化后的向量的点积（即余弦相似度）
    return np.dot(vec1, vec2)


def search_similar_texts(
    query: str, texts: List[str], embedding_model: EmbeddingModel, top_k: int = 5
) -> List[Dict[str, Any]]:
    """搜索相似文本

    Args:
        query: 查询文本
        texts: 文本列表
        embedding_model: 嵌入模型
        top_k: 返回的最相似文本数量

    Returns:
        List[Dict[str, Any]]: 相似文本列表，包含文本和相似度
    """
    # 获取查询文本的嵌入向量
    query_embedding = embedding_model.get_embeddings([query])[0]

    # 获取所有文本的嵌入向量
    text_embeddings = embedding_model.get_embeddings(texts)

    # 计算相似度
    similarities = []
    for i, text_embedding in enumerate(text_embeddings):
        similarity = cosine_similarity(query_embedding, text_embedding)
        similarities.append((i, similarity))

    # 按相似度排序
    similarities.sort(key=lambda x: x[1], reverse=True)

    # 返回top_k个最相似的文本
    results = []
    for i, similarity in similarities[:top_k]:
        results.append({"text": texts[i], "similarity": similarity})

    return results


# 示例用法
if __name__ == "__main__":
    # 创建嵌入模型
    embedding_model = OllamaEmbedding()

    # 测试文本
    texts = [
        "人工智能是研究如何使计算机模拟人类智能的一门学科",
        "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习",
        "深度学习是机器学习的一种方法，使用神经网络进行学习",
        "自然语言处理是人工智能的一个分支，研究计算机与人类语言的交互",
        "计算机视觉是人工智能的一个领域，研究如何让计算机理解图像和视频",
    ]

    # 获取嵌入向量
    embeddings = embedding_model.get_embeddings(texts)
    print(f"嵌入向量维度: {len(embeddings[0])}")

    # 搜索相似文本
    query = "深度学习和神经网络"
    results = search_similar_texts(query, texts, embedding_model, top_k=3)

    print(f"查询: {query}")
    for i, result in enumerate(results):
        print(f"{i+1}. 文本: {result['text']}")
        print(f"   相似度: {result['similarity']:.4f}")
