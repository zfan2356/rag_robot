import logging
import sys
import time
import unittest
from typing import Any

import gradio as gr

# 添加父目录到sys.path，以便能够导入gradio模块
sys.path.append("..")

from gr_app.ref_func import RefFunc, RefModelConfigFunc
from gr_app.refresh_manager import RefreshManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRefFunc(RefFunc[str]):
    """测试用的RefFunc实现类，每次调用时输出hello"""

    def __init__(self):
        self.call_count = 0

    def __call__(self, textbox: str) -> str:
        """
        每次调用时输出hello并更新文本框

        Args:
            textbox: Gradio文本框组件

        Returns:
            更新后的文本框组件
        """
        self.call_count += 1
        message = f"hello - 调用次数: {self.call_count}"
        logger.info(textbox)

        # 更新文本框内容
        return textbox


class TestRefreshManager(unittest.TestCase):
    """测试RefreshManager类"""

    def test_add_function(self):
        """测试添加函数到刷新管理器"""
        manager = RefreshManager()
        test_func = TestRefFunc()

        # 添加函数到管理器
        manager.add_function(test_func, "test", interval=0.1)

        # 验证函数已添加
        self.assertEqual(len(manager.refresh_functions), 1)
        self.assertEqual(manager.refresh_functions[0]["func"], test_func)
        self.assertEqual(manager.refresh_functions[0]["component"], "test")
        self.assertEqual(manager.refresh_functions[0]["interval"], 0.1)
        self.assertEqual(manager.refresh_functions[0]["name"], "TestRefFunc")

    def test_start_stop(self):
        """测试启动和停止刷新管理器"""
        manager = RefreshManager()
        test_func = TestRefFunc()

        # 添加函数到管理器
        manager.add_function(test_func, "test", interval=0.1)

        # 启动管理器
        manager.start()
        self.assertTrue(manager.running)
        self.assertEqual(len(manager.threads), 1)

        # 等待一段时间，让函数执行几次
        time.sleep(0.5)  # 应该执行约5次

        # 停止管理器
        manager.stop()
        self.assertFalse(manager.running)
        self.assertEqual(len(manager.threads), 0)

        # 验证函数被调用了多次
        self.assertGreater(test_func.call_count, 1, "函数应该被调用多次")
        logger.info(f"函数被调用了 {test_func.call_count} 次")

    def test_model_config_func(self):
        """测试模型配置函数"""
        import gradio as gr

        dropdown = gr.Dropdown()
        manager = RefreshManager()
        model_config_func = RefModelConfigFunc()
        manager.add_function(model_config_func, dropdown, interval=1)
        manager.start()
        time.sleep(10)

    def test_context_manager(self):
        """测试上下文管理器接口"""
        test_func = TestRefFunc()

        # 使用上下文管理器
        with RefreshManager() as manager:
            manager.add_function(test_func, "test", interval=0.1)
            self.assertTrue(manager.running)

            # 等待一段时间，让函数执行几次
            time.sleep(0.5)  # 应该执行约5次

        # 上下文结束后，管理器应该已停止
        self.assertFalse(manager.running)

        # 验证函数被调用了多次
        self.assertGreater(test_func.call_count, 1, "函数应该被调用多次")
        logger.info(f"函数被调用了 {test_func.call_count} 次")


def run_manual_test():
    """手动运行测试，观察输出"""
    from gr_app.refresh_manager import refresh_manager

    test_func = TestRefFunc()

    # 添加函数到全局刷新管理器
    refresh_manager.add_function(test_func, "test", interval=0.1)

    # 启动管理器
    refresh_manager.start()

    try:
        # 运行10秒
        logger.info("开始运行，将持续10秒...")
        for i in range(10):
            time.sleep(1)
            logger.info(f"已运行 {i+1} 秒，当前调用次数: {test_func.call_count}")
    finally:
        # 停止管理器
        refresh_manager.stop()
        logger.info(f"测试结束，函数共被调用 {test_func.call_count} 次")


if __name__ == "__main__":
    # 运行单元测试
    unittest.main(argv=["first-arg-is-ignored"], exit=False)

    # 或者运行手动测试
    # run_manual_test()
