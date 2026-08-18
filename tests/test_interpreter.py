import json
import sys
from pathlib import Path
from types import SimpleNamespace


import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import interpreter


class FakeCompletions:
    """模拟 client.chat.completions。"""

    def __init__(self, content: str):
        self.content = content
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs

        message = SimpleNamespace(content=self.content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeClient:
    """模拟 DeepSeek 客户端。"""

    def __init__(self, content: str):
        completions = FakeCompletions(content)
        self.chat = SimpleNamespace(completions=completions)


def test_normal_structured_response_parses_without_real_api(monkeypatch):
    """正常 JSON 可解析，且类别、指标和值能精确对应摘要。"""
    fake_response = {
        "conclusion": "Self-employed 的平均血糖水平最高。",
        "evidence": [
            {
                "category": "Self-employed",
                "field": "平均血糖水平",
                "value": "112.65",
            }
        ],
        "limitations": ["摘要不能支持因果推断。"],
        "next_step": "本周范围内无需扩展分析。",
    }

    fake_client = FakeClient(json.dumps(fake_response, ensure_ascii=False))

    monkeypatch.setattr(
        interpreter,
        "create_client_and_get_model",
        lambda: (fake_client, "fake-deepseek-model"),
    )

    result = interpreter.request_structured_analysis()

    assert result.conclusion == "Self-employed 的平均血糖水平最高。"
    assert result.evidence[0].category == "Self-employed"
    assert result.evidence[0].field == "平均血糖水平"
    assert result.evidence[0].value == "112.65"

    request = fake_client.chat.completions.last_request
    assert request["model"] == "fake-deepseek-model"
    assert request["response_format"] == {"type": "json_object"}
    assert request["stream"] is False


def test_insufficient_evidence_response_states_limitations(monkeypatch):
    """证据不足时说明限制；虚构或错配证据必须被拒绝。"""
    insufficient_response = {
        "conclusion": "现有摘要不足以解释工作类型为什么会导致平均血糖水平不同。",
        "evidence": [
            {
                "category": "Self-employed",
                "field": "平均血糖水平",
                "value": "112.65",
            }
        ],
        "limitations": [
            "证据不足：摘要只提供样本数和平均值，不能支持因果解释。"
        ],
        "next_step": "本周范围内不进行额外统计推断。",
    }

    valid_client = FakeClient(json.dumps(insufficient_response, ensure_ascii=False))

    monkeypatch.setattr(
        interpreter,
        "create_client_and_get_model",
        lambda: (valid_client, "fake-deepseek-model"),
    )

    result = interpreter.request_structured_analysis()

    assert "不足以解释" in result.conclusion
    assert "证据不足" in " ".join(result.limitations)
    assert result.evidence[0].category == "Self-employed"
    assert result.evidence[0].field == "平均血糖水平"
    assert result.evidence[0].value == "112.65"

    mismatched_response = {
        "conclusion": "Private 的样本数为 112.65。",
        "evidence": [
            {
                "category": "Private",
                "field": "样本数",
                "value": "112.65",
            }
        ],
        "limitations": ["该响应用于验证错误证据会被拒绝。"],
        "next_step": "无需继续分析。",
    }

    invalid_client = FakeClient(json.dumps(mismatched_response, ensure_ascii=False))

    monkeypatch.setattr(
        interpreter,
        "create_client_and_get_model",
        lambda: (invalid_client, "fake-deepseek-model"),
    )

    with pytest.raises(interpreter.EvidenceValidationError):
        interpreter.request_structured_analysis()


def test_api_connection_failure_does_not_leak_configuration(monkeypatch, capsys):
    """模拟 API 连接失败，并确认错误输出不包含测试秘密。"""
    from httpx import Request
    from openai import APIConnectionError

    fake_secret = "test_secret_value_should_not_appear"

    def raise_connection_error(prompt_version="v2"):
        raise APIConnectionError(
            message=f"连接失败，配置值为 {fake_secret}",
            request=Request("POST", "https://api.deepseek.com"),
        )

    monkeypatch.setattr(
        interpreter,
        "request_structured_analysis",
        raise_connection_error,
    )

    exit_code = interpreter.main()
    captured = capsys.readouterr()

    assert exit_code == 8
    assert "连接失败" in captured.err
    assert fake_secret not in captured.out
    assert fake_secret not in captured.err
