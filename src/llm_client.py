import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def create_client_and_get_model() -> tuple[OpenAI, str]:
    """读取 DeepSeek 配置，并创建兼容 API 的客户端。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    model = os.getenv("DEEPSEEK_MODEL")
    base_url = os.getenv("DEEPSEEK_BASE_URL")

    if not api_key:
        raise ValueError("缺少 DEEPSEEK_API_KEY。请在 .env 文件中配置它。")

    if not model:
        raise ValueError("缺少 DEEPSEEK_MODEL。请在 .env 文件中配置它。")

    if not base_url:
        raise ValueError("缺少 DEEPSEEK_BASE_URL。请在 .env 文件中配置它。")

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def get_first_response(client: OpenAI, model: str) -> str:
    """发送一次非流式 DeepSeek 请求，并返回完整文本。"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一名简洁、准确的学习助手。只用一句中文回答。",
            },
            {
                "role": "user",
                "content": "用一句话解释：程序为什么要从环境变量读取 API Key？",
            },
        ],
        stream=False,
    )

    output_text = response.choices[0].message.content
    if not output_text:
        raise RuntimeError("模型没有返回文本内容。")

    return output_text


def main() -> int:
    try:
        client, model = create_client_and_get_model()
        text = get_first_response(client, model)
    except ValueError as error:
        print(f"配置错误：{error}", file=sys.stderr)
        return 2
    except APITimeoutError:
        print("请求超时：请检查网络后重试。", file=sys.stderr)
        return 3
    except APIConnectionError:
        print("连接失败：请检查网络或 DEEPSEEK_BASE_URL 配置。", file=sys.stderr)
        return 4
    except RateLimitError:
        print("请求被限制（429）：请检查 DeepSeek 额度或等待后重试。", file=sys.stderr)
        return 5
    except APIStatusError as error:
        print(f"上游 API 返回错误，状态码：{error.status_code}。", file=sys.stderr)
        return 6
    except RuntimeError as error:
        print(f"响应错误：{error}", file=sys.stderr)
        return 7

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
