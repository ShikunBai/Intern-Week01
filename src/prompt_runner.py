import json
import sys
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from llm_client import create_client_and_get_model


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summary.json"


def build_prompt(version: str) -> str:
    """读取 Prompt 模板，并将摘要填入占位符。"""
    prompt_path = PROJECT_ROOT / "prompts" / f"{version}.txt"

    if not prompt_path.exists():
        raise ValueError(f"找不到 Prompt 文件：{prompt_path}")

    template = prompt_path.read_text(encoding="utf-8")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2)

    return template.replace("{summary_json}", summary_text)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"v1", "v2"}:
        print("用法：python src/prompt_runner.py v1 或 python src/prompt_runner.py v2")
        return 1

    version = sys.argv[1]

    try:
        prompt = build_prompt(version)
        client, model = create_client_and_get_model()

        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "developer",
                    "content": "你是一名数据分析助手。请使用中文回答。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
    except ValueError as error:
        print(f"配置或文件错误：{error}", file=sys.stderr)
        return 2
    except APITimeoutError:
        print("请求超时：请检查网络后重试。", file=sys.stderr)
        return 3
    except APIConnectionError:
        print("连接失败：请检查网络或 OPENAI_BASE_URL 配置。", file=sys.stderr)
        return 4
    except RateLimitError:
        print("请求被限制（429）：请检查 API 额度或等待后重试。", file=sys.stderr)
        return 5
    except APIStatusError as error:
        print(f"上游 API 返回错误，状态码：{error.status_code}。", file=sys.stderr)
        return 6

    output_text = response.output_text.strip()
    if not output_text:
        print("模型没有返回文本内容。", file=sys.stderr)
        return 7

    output_path = PROJECT_ROOT / "outputs" / f"{version}-response.txt"
    output_path.write_text(output_text + "\n", encoding="utf-8")

    print(f"{version.upper()} 输出已保存：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
