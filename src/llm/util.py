import subprocess
import time
from typing import Any, Dict, List, Optional

import requests


class OllamaManager:
    def __init__(
        self,
        target_model: str = "deepseek-r1:7b",
        base_url: str = "http://localhost:11434",
        timeout: float = 3.0,
    ):
        """
        Ollama 服务管理类

        :param target_model: 目标模型名称
        :param base_url: Ollama 服务地址
        :param timeout: 请求超时时间（秒）
        """
        self.target_model = target_model
        self.base_url = base_url
        self.timeout = timeout

    def check_status(self) -> Dict[str, Any]:
        """
        检查服务状态和模型状态
        返回示例：
        {
            'service_available': True,
            'model_available': True,
            'local_models': ['llama2', 'deepseek-r1:7b'],
            'detail': '服务运行正常，模型 deepseek-r1:7b 已存在'
        }
        """
        result = {
            "service_available": False,
            "model_available": False,
            "local_models": [],
            "detail": "",
        }

        try:
            # 检查基础服务状态
            health_resp = requests.get(self.base_url, timeout=self.timeout)
            result["service_available"] = health_resp.status_code == 200

            if not result["service_available"]:
                result["detail"] = f"服务异常，HTTP状态码：{health_resp.status_code}"
                return result

            # 获取模型列表
            models_resp = requests.get(
                f"{self.base_url}/api/tags", timeout=self.timeout
            )
            models_resp.raise_for_status()

            models_data = models_resp.json()
            local_models = [model["name"] for model in models_data.get("models", [])]
            result["local_models"] = local_models

            # 检查目标模型
            model_exists = any(
                self.target_model in model_name for model_name in local_models
            )
            result["model_available"] = model_exists

            # 生成状态描述
            status_msg = "服务运行正常，"
            if model_exists:
                status_msg += f"模型 {self.target_model} 已存在"
            else:
                status_msg += f"但模型 {self.target_model} 未找到"
            result["detail"] = status_msg

        except requests.exceptions.ConnectionError:
            result["detail"] = "无法连接到 Ollama 服务，请检查是否已启动"
        except requests.exceptions.Timeout:
            result["detail"] = f"连接超时（{self.timeout}s），请检查网络或调整超时时间"
        except Exception as e:
            result["detail"] = f"检测时发生意外错误：{str(e)}"

        return result

    def change_target_model(self, new_model: str) -> bool:
        """
        修改目标模型并验证有效性

        :param new_model: 新的目标模型名称
        :return: 是否修改成功
        """
        if not isinstance(new_model, str) or len(new_model.strip()) == 0:
            print("无效的模型名称")
            return False

        # 保留旧模型名称用于回滚
        previous_model = self.target_model
        self.target_model = new_model.strip()

        # 验证新模型是否存在于本地
        if not self.check_status()["model_available"]:
            print(f"警告：模型 {new_model} 未在本地找到")
            # 是否自动回滚取决于需求，这里保持修改但给出警告
            self.target_model = previous_model

        return True

    def start_service(self, retries: int = 3) -> bool:
        """
        自动启动 Ollama 服务

        :param retries: 最大重试次数
        :return: 是否启动成功
        """
        try:
            status = self.check_status()
            if status["service_available"]:
                return True

            # 启动服务进程
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # 等待服务就绪
            for _ in range(retries):
                if self.check_status()["service_available"]:
                    return True
                time.sleep(1)
            return False
        except Exception as e:
            print(f"启动服务失败：{str(e)}")
            return False

    def ensure_model(self, download_timeout: int = 600) -> bool:
        """
        确保目标模型可用

        :param download_timeout: 下载超时时间（秒）
        :return: 模型是否可用
        """
        status = self.check_status()
        if status["model_available"]:
            return True

        print(f"开始下载模型 {self.target_model}...")
        try:
            result = subprocess.run(
                ["ollama", "pull", self.target_model],
                capture_output=True,
                text=True,
                timeout=download_timeout,
            )

            if result.returncode == 0:
                return True

            print(f"下载失败：{result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            print("下载超时")
            return False
        except Exception as e:
            print(f"下载过程中发生错误：{str(e)}")
            return False
