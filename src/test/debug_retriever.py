import logging
import os
import sys

from src.embd import OllamaEmbedding
from src.rag import DocumentRetriever, DocumentStore

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """测试DocumentRetriever类的基本功能"""
    try:
        # 使用测试数据库URL
        test_db_url = os.environ.get(
            "TEST_DB_URL", "mysql+pymysql://root:123456@localhost/rag_robot"
        )

        logger.info(f"使用数据库URL: {test_db_url}")

        # 创建嵌入模型
        try:
            embedding_model = OllamaEmbedding(
                model_name="nomic-embed-text", normalize_vectors=True
            )
            logger.info("成功创建嵌入模型")
        except Exception as e:
            logger.error(f"创建嵌入模型时出错: {str(e)}")
            raise

        # 创建DocumentStore实例
        try:
            doc_store = DocumentStore(
                embedding_model=embedding_model,
                db_url=test_db_url,
                chunk_size=500,
                chunk_overlap=100,
            )
            logger.info("成功创建DocumentStore实例")
        except Exception as e:
            logger.error(f"创建DocumentStore实例时出错: {str(e)}")
            raise

        # 创建DocumentRetriever实例
        try:
            retriever = DocumentRetriever(
                document_store=doc_store,
                embedding_model=embedding_model,
                top_k=3,
                similarity_threshold=0.5,
            )
            logger.info("成功创建DocumentRetriever实例")
        except Exception as e:
            logger.error(f"创建DocumentRetriever实例时出错: {str(e)}")
            raise

        # 测试文档
        test_docs = [
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
        test_doc_ids = []

        # 添加测试文档
        try:
            for doc in test_docs:
                doc_id = doc_store.add_document(
                    content=doc["content"], title=doc["title"]
                )
                test_doc_ids.append(doc_id)
            logger.info(f"成功添加 {len(test_doc_ids)} 个测试文档")
        except Exception as e:
            logger.error(f"添加测试文档时出错: {str(e)}")
            raise

        # 更新检索器缓存
        try:
            retriever.update_cache()
            logger.info("成功更新检索器缓存")
        except Exception as e:
            logger.error(f"更新检索器缓存时出错: {str(e)}")
            raise

        # 测试检索功能
        try:
            query = "深度学习和神经网络"
            logger.info(f"执行查询: '{query}'")

            results = retriever.get_relevant_documents(query)

            logger.info(f"检索到 {len(results)} 个相关文档")
            for i, doc in enumerate(results):
                logger.info(f"文档 {i+1}:")
                logger.info(f"  相似度: {doc.metadata['similarity']:.4f}")
                logger.info(f"  标题: {doc.metadata['title']}")
                logger.info(f"  内容: {doc.page_content[:100]}...")
        except Exception as e:
            logger.error(f"检索文档时出错: {str(e)}")
            raise

        # 清理测试文档
        try:
            for doc_id in test_doc_ids:
                doc_store.delete_document(doc_id)
            logger.info(f"成功删除 {len(test_doc_ids)} 个测试文档")
        except Exception as e:
            logger.error(f"删除测试文档时出错: {str(e)}")
            raise

        logger.info("测试完成")

    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
