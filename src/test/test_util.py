from unittest.mock import Mock, patch

import pytest
import requests

from ollama.util import check_ollama_status


@pytest.fixture
def mock_requests():
    with patch("requests.get") as mock_get, patch("requests.post"):
        yield mock_get


def test_service_available_and_model_exists(mock_requests):
    """测试服务正常且模型存在的情况"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [
        {},
        {"models": [{"name": "deepseek-r1:7b"}, {"name": "llama2"}]},
    ]
    mock_requests.return_value = mock_response

    result = check_ollama_status("deepseek-r1:7b")

    assert result["service_available"] is True
    assert result["model_available"] is True
    assert "deepseek-r1:7b" in result["local_models"]
    assert "服务运行正常" in result["detail"]


def test_service_available_but_model_missing(mock_requests):
    """测试服务正常但模型不存在的情况"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [{}, {"models": [{"name": "llama2"}]}]
    mock_requests.return_value = mock_response

    result = check_ollama_status("deepseek-r1:7b")

    assert result["service_available"] is True
    assert result["model_available"] is False
    assert "deepseek-r1:7b" not in result["local_models"]
    assert "未找到" in result["detail"]


def test_service_unavailable():
    """测试服务未启动的情况"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError

        result = check_ollama_status()

        assert result["service_available"] is False
        assert result["model_available"] is False
        assert "无法连接" in result["detail"]


def test_http_error_response(mock_requests):
    """测试HTTP错误状态码"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_requests.return_value = mock_response

    result = check_ollama_status()

    assert result["service_available"] is False
    assert "HTTP状态码：500" in result["detail"]


def test_request_timeout():
    """测试请求超时情况"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout

        result = check_ollama_status(timeout=0.1)

        assert result["service_available"] is False
        assert "连接超时" in result["detail"]


def test_unexpected_exception():
    """测试意外异常"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Random error")

        result = check_ollama_status()

        assert result["service_available"] is False
        assert "意外错误" in result["detail"]


def test_partial_model_name_match():
    """测试模型名称模糊匹配"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [{}, {"models": [{"name": "deepseek-r1:7b-q4_0"}]}]

    with patch("requests.get", return_value=mock_response):
        result = check_ollama_status("deepseek-r1:7b")

        assert result["model_available"] is True
        assert "deepseek-r1:7b-q4_0" in result["local_models"]


def test_custom_base_url():
    """测试自定义服务地址"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200

        check_ollama_status(base_url="http://custom-host:11434")

        mock_get.assert_any_call(
            "http://custom-host:11434/", timeout=pytest.approx(3.0)
        )
