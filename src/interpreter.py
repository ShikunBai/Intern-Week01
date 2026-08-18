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
      "category": "摘要中完全一致的类别名称",
      "field": "样本数或平均血糖水平",
      "value": "该类别和指标对应的单个原始值"
    }
  ],
  "limitations": ["限制说明"],
  "next_step": "下一步建议"
}

evidence 的规则：
- category 必须与数据摘要中的“类别”完全一致，例如 "Self-employed"。
- field 只能是 "样本数" 或 "平均血糖水平"。
- value 必须是该 category 和该 field 在摘要中对应的单个原始值。
- value 不得添加单位、解释文字或摘要中不存在的数字。
"""


class EvidenceValidationError(ValueError):
    """结构正确但证据无法与摘要中的类别、指标和值精确对应时抛出。"""


def normalize_value(value: Any) -> tuple[str, Any]:
    """将数字和文本转换为便于比较的形式。"""
    text = str(value).strip()

    try:
        return "number", Decimal(text)
    except InvalidOperation:
        return "text", text


def build_evidence_index(
    summary: dict[str, Any],
) -> dict[tuple[str, str], tuple[str, Any]]:
    """建立“类别 + 指标 -> 值”的可复核索引。"""
    groups = summary.get("类别汇总")

    if not isinstance(groups, list):
        raise ValueError("summary.json 缺少有效的“类别汇总”列表。")

    evidence_index: dict[tuple[str, str], tuple[str, Any]] = {}

    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("summary.json 的“类别汇总”包含无效记录。")

        try:
            category = str(group["类别"]).strip()

            for field in ("样本数", "平均血糖水平"):
                evidence_index[(category, field)] = normalize_value(group[field])
        except KeyError as error:
            raise ValueError(
                f"summary.json 的类别记录缺少必要字段：{error}"
            ) from error

    return evidence_index


def validate_evidence_associations(
    result: AnalysisResult,
    summary: dict[str, Any],
) -> None:
    """确认每条证据的类别、指标和值三者能在摘要中精确对应。"""
    evidence_index = build_evidence_index(summary)
    invalid_evidence: list[str] = []

    for item in result.evidence:
        key = (item.category.strip(), item.field)
        expected_value = evidence_index.get(key)
        actual_value = normalize_value(item.value)

        if expected_value is None:
            invalid_evidence.append(
                f"类别“{item.category}”与指标“{item.field}”无法在摘要中定位"
            )
        elif actual_value != expected_value:
            invalid_evidence.append(
                f"类别“{item.category}”、指标“{item.field}”"
                f"应为“{expected_value[1]}”，但模型返回“{item.value}”"
            )

    if invalid_evidence:
        raise EvidenceValidationError("；".join(invalid_evidence))


def request_structured_analysis(
    prompt_version: str = "v2",
) -> AnalysisResult:
    """调用 DeepSeek JSON Output，并解析和校验证据关联。"""
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
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
    validate_evidence_associations(result, summary)
    return result


def main() -> int:
    prompt_version = sys.argv[1] if len(sys.argv) == 2 else "v2"

    try:
        result = request_structured_analysis(prompt_version)
    except EvidenceValidationError as error:
        print(f"证据关联校验失败：{error}", file=sys.stderr)
        return 2
    except ValidationError as error:
        print(f"结构化输出验证失败：{error}", file=sys.stderr)
        return 3
    except json.JSONDecodeError as error:
        print(f"摘要文件不是有效 JSON：{error}", file=sys.stderr)
        return 4
    except OSError as error:
        print(f"文件读取或写入失败：{error}", file=sys.stderr)
        return 5
    except ValueError as error:
        print(f"配置或文件错误：{error}", file=sys.stderr)
        return 6
    except APITimeoutError:
        print("请求超时：请检查网络后重试。", file=sys.stderr)
        return 7
    except APIConnectionError:
        print("连接失败：请检查网络或 DEEPSEEK_BASE_URL 配置。", file=sys.stderr)
        return 8
    except RateLimitError:
        print("请求被限制（429）：请检查 DeepSeek 额度或等待后重试。", file=sys.stderr)
        return 9
    except APIStatusError as error:
        print(f"上游 API 返回错误，状态码：{error.status_code}。", file=sys.stderr)
        return 10
    except RuntimeError as error:
        print(f"响应错误：{error}", file=sys.stderr)
        return 11

    OUTPUT_PATH.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"结构化结果已保存：{OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())