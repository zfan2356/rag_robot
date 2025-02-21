import subprocess
import time
from typing import Any, Dict, Tuple

import requests


def check_ollama_status(
    target_model: str = "deepseek-r1:7b",
    base_url: str = "http://localhost:11434",
    timeout: float = 3.0,
) -> Dict[str, Any]:
    """
    检查 Ollama 服务状态和模型状态
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
        # 检查服务是否运行
        health_resp = requests.get(f"{base_url}/", timeout=timeout)
        if health_resp.status_code == 200:
            result["service_available"] = True
        else:
            result["detail"] = f"服务异常，HTTP状态码：{health_resp.status_code}"
            return result

        # 获取本地模型列表
        models_resp = requests.get(f"{base_url}/api/tags", timeout=timeout)
        models_resp.raise_for_status()

        models_data = models_resp.json()
        local_models = [model["name"] for model in models_data.get("models", [])]
        result["local_models"] = local_models

        # 检查目标模型是否存在
        model_exists = any(target_model in model_name for model_name in local_models)
        result["model_available"] = model_exists

        # 生成详细信息
        if model_exists:
            result["detail"] = f"服务运行正常，模型 {target_model} 已存在"
        else:
            result["detail"] = f"服务运行正常，但模型 {target_model} 未找到"

    except requests.exceptions.ConnectionError:
        result["detail"] = "无法连接到 Ollama 服务，请检查是否已启动"
    except requests.exceptions.Timeout:
        result["detail"] = f"连接超时（{timeout}s），请检查网络或调整超时时间"
    except Exception as e:
        result["detail"] = f"检测时发生意外错误：{str(e)}"

    return result


def auto_start_ollama():
    try:
        # 检测服务状态
        status = check_ollama_status(timeout=1.0)
        if status["service_available"]:
            return True

        # 启动服务
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # 等待启动完成
        for _ in range(10):
            if check_ollama_status(timeout=1.0)["service_available"]:
                return True
            time.sleep(1)
        return False
    except:
        return False


def ensure_model_available(target_model: str):
    status = check_ollama_status(target_model)
    if status["model_available"]:
        return True

    print(f"开始下载模型 {target_model}...")
    try:
        result = subprocess.run(
            ["ollama", "pull", target_model],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            return True
        print(f"下载失败：{result.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("下载超时")
        return False
