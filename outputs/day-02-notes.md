# Day 2 学习笔记：第一次 DeepSeek 非流式 API 调用

## 当前状态

已完成 `src/llm_client.py`，并成功完成一次真实 DeepSeek 非流式文本调用。

本项目最初计划学习 OpenAI Responses API，但实际改用 DeepSeek。因此程序使用 OpenAI Python SDK 的兼容接口 `client.chat.completions.create(...)`，而不是 `client.responses.create(...)`。

真实模型响应已保存到：

    outputs/first-response.txt

缺少配置时的错误样例已保存到：

    outputs/first-error-example.txt

## 1. 输入消息的作用

程序向 `client.chat.completions.create(...)` 传入 `messages`。

`messages` 是发送给模型的消息列表。本项目将两类信息分开：

- `system`：角色说明，规定模型应当“简洁、准确，并只用一句中文回答”。
- `user`：具体任务，即“用一句话解释程序为什么要从环境变量读取 API Key”。

`system` 消息用于约束模型的回答方式；`user` 消息用于说明本次要完成的具体任务。

程序设置：

    stream=False

表示使用非流式调用：程序等待模型完整生成回答后，再一次性读取结果。

## 2. 模型配置的作用

模型名称不直接写死在 Python 代码中，而是从 `.env` 文件中的以下变量读取：

    DEEPSEEK_MODEL
    DEEPSEEK_BASE_URL
    DEEPSEEK_API_KEY

其中：

- `DEEPSEEK_MODEL`：指定本次调用使用的模型。
- `DEEPSEEK_BASE_URL`：指定 DeepSeek API 地址。
- `DEEPSEEK_API_KEY`：用于身份认证。

这样可以在不修改 Python 代码的情况下更换模型或 API 地址。真实 API Key 保存在 `.env` 中，并被 `.gitignore` 忽略，因此不会提交到 Git 或 GitHub。

## 3. 模型响应内容的作用

`client.chat.completions.create(...)` 返回一个 response 对象。

本项目通过以下路径读取模型生成的完整文本：

    response.choices[0].message.content

程序将该文本输出到终端，并保存到：

    outputs/first-response.txt

本次真实调用成功后得到的回答为：

    从环境变量读取API Key可以避免硬编码进代码，降低泄露风险，同时便于在不同环境中灵活配置。

## 4. 已验证的错误处理

当 `.env` 不存在，或缺少 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL` 中任意配置时，程序会返回可理解的配置错误提示，例如：

    配置错误：缺少 DEEPSEEK_API_KEY。请在项目根目录的 .env 文件中配置它。

程序还显式处理以下情况：

- 请求超时；
- 网络连接失败；
- 请求额度或频率限制（429）；
- 上游 API 返回错误；
- 模型未返回有效文本。

错误信息用于帮助定位问题，但不会输出 API Key 或其他敏感配置。

## 5. 本日结论

本日完成了从环境变量读取配置、构造角色说明和用户任务、发送一次非流式 LLM 请求、读取模型完整回答以及处理常见错误的完整链路。

虽然本项目最终使用的是 DeepSeek 兼容接口，而不是 OpenAI Responses API，但学习到的核心概念一致：输入消息决定模型收到的信息，模型配置决定调用目标，响应对象提供模型生成的结果，错误处理保证程序在异常情况下仍能安全、清晰地反馈问题。