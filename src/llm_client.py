import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def create_client_and_get_model() -> tuple[OpenAI, str]:
    """读取配置，并创建 OpenAI 客户端。"""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key:
        raise ValueError("缺少 OPENAI_API_KEY。请在项目根目录的 .env 文件中配置它。")

    if not model:
        raise ValueError("缺少 OPENAI_MODEL。请在项目根目录的 .env 文件中配置它。")

    client_options = {"api_key": api_key}
    if base_url:
        client_options["base_url"] = base_url

    return OpenAI(**client_options), model


def get_first_response(client: OpenAI, model: str) -> str:
    """发送一次非流式请求，并返回完整文本。"""
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "developer",
                "content": "你是一名简洁、准确的学习助手。只用一句中文回答。",
            },
            {
                "role": "user",
                "content": "用一句话解释：程序为什么要从环境变量读取 API Key？",
            },
        ],
    )
    return response.output_text


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
        print("连接失败：请检查网络或 OPENAI_BASE_URL 配置。", file=sys.stderr)
        return 4
    except APIStatusError as error:
        print(f"上游 API 返回错误，状态码：{error.status_code}。", file=sys.stderr)
        return 5

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
