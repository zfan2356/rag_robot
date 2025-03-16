import logging
import threading
import time
from typing import Any, Dict, Generic, List, Optional, TypeVar

from gr_app.ref_func import RefFunc

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

T = TypeVar("T")

__all__ = ["refresh_manager"]


class RefreshManager:
    """
    刷新管理器，用于定期调用RefFunc类型的函数

    该管理器会为每个添加的RefFunc创建一个线程，并每隔一定时间调用一次
    """

    def __init__(self):
        """初始化刷新管理器"""
        self.refresh_functions: List[Dict[str, Any]] = []
        self.threads: List[threading.Thread] = []
        self.running = False
        self.stop_event = threading.Event()

    def add_function(
        self, refresh_func: RefFunc, component: Any, interval: float = 0.1
    ) -> None:
        """
        添加一个RefFunc类型的函数到刷新管理器

        Args:
            refresh_func: RefFunc类型的函数
            component: 要传递给RefFunc.__call__的组件
            interval: 刷新间隔（秒）
        """
        # 添加函数信息到列表
        func_info = {
            "func": refresh_func,
            "component": component,
            "interval": interval,
            "name": refresh_func.__class__.__name__,
        }
        self.refresh_functions.append(func_info)

        # 如果管理器正在运行，立即为新函数创建线程
        if self.running:
            self._create_thread_for_function(func_info)

        logger.info(f"添加刷新函数: {func_info['name']}")

    def start(self):
        """启动所有刷新函数的线程"""
        if self.running:
            logger.warning("刷新管理器已经在运行中")
            return

        self.running = True
        self.stop_event.clear()

        # 为每个函数创建线程
        for func_info in self.refresh_functions:
            self._create_thread_for_function(func_info)

        logger.info(f"启动刷新管理器，共 {len(self.refresh_functions)} 个函数")

    def stop(self):
        """停止所有刷新函数的线程"""
        if not self.running:
            logger.warning("刷新管理器未在运行")
            return

        self.running = False
        self.stop_event.set()

        # 等待所有线程结束
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)

        self.threads = []
        logger.info("停止刷新管理器")

    def _create_thread_for_function(self, func_info: Dict[str, Any]):
        """为函数创建线程

        Args:
            func_info: 函数信息字典
        """
        thread = threading.Thread(
            target=self._run_function_loop, args=(func_info,), daemon=True
        )
        thread.start()
        self.threads.append(thread)

    def _run_function_loop(self, func_info: Dict[str, Any]):
        """运行函数循环

        Args:
            func_info: 函数信息字典
        """
        refresh_func = func_info["func"]
        component = func_info["component"]
        interval = func_info["interval"]
        name = func_info["name"]

        logger.info(f"启动刷新函数线程: {name}")

        while not self.stop_event.is_set():
            try:
                start_time = time.time()

                # 调用RefFunc的__call__方法
                refresh_func(component)

            except Exception as e:
                logger.error(f"刷新函数 {name} 执行出错: {str(e)}")

            # 计算需要等待的时间
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)

            # 使用stop_event等待，这样可以更快地响应停止请求
            if not self.stop_event.wait(sleep_time):
                continue
            else:
                break

        logger.info(f"停止刷新函数线程: {name}")

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()


# 创建全局刷新管理器实例
refresh_manager = RefreshManager()
