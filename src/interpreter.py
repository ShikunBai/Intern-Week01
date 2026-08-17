import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from llm_client import create_client_and_get_model
from prompt_runner import build_prompt
from schemas import AnalysisResult


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summary.json"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "structured-result.json"

STRUCTURED_SYSTEM_PROMPT = """
你是一名谨慎的数据摘要解读助手。

必须只使用用户消息中的数据摘要作为事实来源。
输出必须是一个合法 JSON 对象，不要使用 Markdown 代码块，不要添加 JSON 以外的文字。

JSON 对象必须包含且只能包含以下字段：
{
  "conclusion": "基于摘要的结论",
  "evidence": [
    {
      "metric": "指标或类别说明",
      "value": "摘要中可直接找到的单个值"
    }
  ],
  "limitations": ["限制说明"],
  "next_step": "下一步建议"
}

evidence 中的 value 必须是数据摘要中的单个原始值，例如：
"112.65"、"2925"、"Self-employed"。
不得添加单位、解释文字或摘要中不存在的数字。
"""


class EvidenceValidationError(ValueError):
    """结构正确但证据值无法在摘要中定位时抛出。"""


def normalize_value(value: Any) -> tuple[str, Any]:
    """将数字和文本转换为便于比较的形式。"""
    text = str(value).strip()

    try:
        return "number", Decimal(text)
    except InvalidOperation:
        return "text", text


def collect_summary_values(value: Any) -> set[tuple[str, Any]]:
    """递归收集 summary.json 中所有实际值。"""
    collected_values: set[tuple[str, Any]] = set()

    if isinstance(value, dict):
        for child_value in value.values():
            collected_values.update(collect_summary_values(child_value))
    elif isinstance(value, list):
        for child_value in value:
            collected_values.update(collect_summary_values(child_value))
    else:
        collected_values.add(normalize_value(value))

    return collected_values


def validate_evidence_values(result: AnalysisResult, summary: dict) -> None:
    """确认每条 evidence.value 都能在 summary.json 中找到。"""
    available_values = collect_summary_values(summary)
    invalid_values = [
        item.value
        for item in result.evidence
        if normalize_value(item.value) not in available_values
    ]

    if invalid_values:
        joined_values = "、".join(invalid_values)
        raise EvidenceValidationError(
            f"结构化结果中的证据值无法在 summary.json 中定位：{joined_values}"
        )


def request_structured_analysis() -> AnalysisResult:
    """调用 DeepSeek JSON Output，并解析为 Pydantic 对象。"""
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    prompt_version = sys.argv[1] if len(sys.argv) == 2 else "v2"
    prompt = build_prompt(prompt_version)
    client, model = create_client_and_get_model()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": STRUCTURED_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
        stream=False,
    )

    if not response.choices or not response.choices[0].message.content:
        raise RuntimeError("模型没有返回 JSON 内容。")

    result = AnalysisResult.model_validate_json(response.choices[0].message.content)
    validate_evidence_values(result, summary)
    return result


def main() -> int:
    try:
        result = request_structured_analysis()
    except EvidenceValidationError as error:
        print(f"证据校验失败：{error}", file=sys.stderr)
        return 2
    except ValidationError as error:
        print(f"结构化输出验证失败：{error}", file=sys.stderr)
        return 3
    except ValueError as error:
        print(f"配置或文件错误：{error}", file=sys.stderr)
        return 4
    except json.JSONDecodeError as error:
        print(f"摘要文件不是有效 JSON：{error}", file=sys.stderr)
        return 5
    except APITimeoutError:
        print("请求超时：请检查网络后重试。", file=sys.stderr)
        return 6
    except APIConnectionError:
        print("连接失败：请检查网络或 DEEPSEEK_BASE_URL 配置。", file=sys.stderr)
        return 7
    except RateLimitError:
        print("请求被限制（429）：请检查 DeepSeek 额度或等待后重试。", file=sys.stderr)
        return 8
    except APIStatusError as error:
        print(f"上游 API 返回错误，状态码：{error.status_code}。", file=sys.stderr)
        return 9
    except RuntimeError as error:
        print(f"响应错误：{error}", file=sys.stderr)
        return 10

    OUTPUT_PATH.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"结构化结果已保存：{OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
