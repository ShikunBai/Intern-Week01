import json
import sys
from pathlib import Path
from types import SimpleNamespace

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
    """正常 JSON 能解析为 AnalysisResult，且使用的是假客户端。"""
    fake_response = {
        "conclusion": "Self-employed 的平均血糖水平最高。",
        "evidence": [
            {
                "metric": "Self-employed 平均血糖水平",
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
    monkeypatch.setattr(interpreter.sys, "argv", ["interpreter.py"])

    result = interpreter.request_structured_analysis()

    assert result.conclusion == "Self-employed 的平均血糖水平最高。"
    assert result.evidence[0].value == "112.65"
    assert result.limitations == ["摘要不能支持因果推断。"]

    request = fake_client.chat.completions.last_request
    assert request["model"] == "fake-deepseek-model"
    assert request["response_format"] == {"type": "json_object"}
    assert request["stream"] is False
def test_insufficient_evidence_response_states_limitations(monkeypatch):
    """证据不足时必须说明限制，且证据值仍需来自 summary.json。"""
    fake_response = {
        "conclusion": "现有摘要不足以解释工作类型为什么会导致平均血糖水平不同。",
        "evidence": [
            {
                "metric": "Self-employed 平均血糖水平",
                "value": "112.65",
            }
        ],
        "limitations": [
            "证据不足：摘要只提供样本数和平均值，不能支持因果解释。"
        ],
        "next_step": "本周范围内不进行额外统计推断。",
    }

    fake_client = FakeClient(json.dumps(fake_response, ensure_ascii=False))

    monkeypatch.setattr(
        interpreter,
        "create_client_and_get_model",
        lambda: (fake_client, "fake-deepseek-model"),
    )
    monkeypatch.setattr(interpreter.sys, "argv", ["interpreter.py"])

    result = interpreter.request_structured_analysis()

    assert "不足以解释" in result.conclusion
    assert "证据不足" in " ".join(result.limitations)
    assert result.evidence[0].value == "112.65"
def test_api_connection_failure_does_not_leak_configuration(monkeypatch, capsys):
    """模拟 API 连接失败，并确认错误输出不包含配置秘密。"""
    from httpx2 import Request
    from openai import APIConnectionError

    fake_secret = "dsk-test-secret-must-not-appear"

    def raise_connection_error():
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

    assert exit_code == 7
    assert "连接失败" in captured.err
    assert fake_secret not in captured.out
    assert fake_secret not in captured.err
