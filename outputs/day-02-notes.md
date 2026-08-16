# Day 2 学习笔记：第一次 Responses API 调用

## 当前状态

已完成 `src/llm_client.py` 的基础代码，并验证了缺少 API 配置时的受控错误提示。

真实 API Key 和模型尚未配置，因此真实模型调用与 `outputs/first-response.txt` 尚待完成。

## 1. 输入（input）的作用

程序向 `client.responses.create(...)` 传入 `input`。

`input` 是发送给模型的消息列表。本项目将两类信息分开：

- `developer`：角色说明，规定模型应当“简洁、准确，并只用一句中文回答”。
- `user`：具体任务，即“用一句话解释程序为什么要从环境变量读取 API Key”。

角色说明用于约束回答方式；用户任务用于说明本次要完成什么。

## 2. 模型配置的作用

模型名称不直接写死在 Python 代码中，而是从 `.env` 文件中的 `OPENAI_MODEL` 读取。

这样可以在不修改代码的情况下更换模型。API Key 也从 `.env` 中的 `OPENAI_API_KEY` 读取，避免把密钥写进代码或提交到仓库。

## 3. response.output_text 的作用

`client.responses.create(...)` 返回一个 response 对象。

本项目通过 `response.output_text` 获取模型生成的完整文本，并使用 `print(text)` 输出到终端。

真实调用成功后，将用下面命令把输出保存为文件：

    python src/llm_client.py > outputs/first-response.txt

## 4. 已验证的错误处理

当 `.env` 不存在或缺少 `OPENAI_API_KEY` 时，程序会显示：

    配置错误：缺少 OPENAI_API_KEY。请在项目根目录的 .env 文件中配置它。

该错误样例已保存到：

    outputs/first-error-example.txt

程序还预先处理了以下情况：

- 请求超时；
- 网络连接失败；
- 上游 API 返回错误。

错误信息不会显示 API Key。
