# Data Summary Interpreter

本项目是第 1 周的学习作业。

程序使用 pandas 计算一份小型 CSV 数据的确定性摘要，再使用 LLM 生成一份有证据约束的结构化解读。
职责边界是：程序负责计算，LLM 负责解释.

## 项目目标

唯一分析问题是：

> 不同工作类型的平均血糖水平和样本量有什么差异？

项目实现了以下内容：

- 使用 DeepSeek API 完成非流式文本调用。
- 使用 pandas 生成可复核的 `outputs/summary.json`。
- 保留 V1、V2 两个 Prompt，并记录对比结果。
- 使用 Pydantic 定义强类型的 `AnalysisResult`。
- 检查结构化结果中 `evidence.value` 是否能在 `summary.json` 中定位。
- 提供 4 个无需网络和真实 API Key 的离线测试。

## 数据来源与字段含义

本项目使用 `data/stroke_data.csv`。

- 数据集名称：Stroke Prediction Dataset（中风预测数据集）
- 原始发布页：<https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset>
- `work_type`：类别字段，表示工作类型。
- `avg_glucose_level`：数值字段，表示平均血糖水平。

## DeepSeek 改编说明

原学习计划要求使用 OpenAI Responses API 的 `responses.create(...)`、`responses.parse(...)` 和 `response.output_parsed`。

本项目因实际使用 DeepSeek，改为使用 OpenAI Python SDK 的兼容接口`client.chat.completions.create(...)`。结构化输出使用 DeepSeek JSON Output，再通过 Pydantic 的 `model_validate_json()` 解析为 `AnalysisResult`。

因此，本项目实现了“结构化结果 + Pydantic 验证 + 证据值核对”，但不使用 OpenAI 原生的 `response.output_parsed`。

## 项目结构

    data/
        stroke_data.csv
    outputs/
        summary.json
        metric-check.md
        first-response.txt
        v1-response.txt
        v2-response.txt
        prompt-comparison.md
        structured-success-result.json
        insufficient-evidence-result.json
        test-results.md
        reflection.md
    prompts/
        v1.txt
        v2.txt
        insufficient-evidence.txt
    src/
        data_summary.py
        llm_client.py
        prompt_runner.py
        schemas.py
        interpreter.py
        list_models.py
    tests/
        test_data_summary.py
        test_interpreter.py

## 安装

在项目根目录执行：

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

## 环境变量配置

复制示例文件：

    cp .env.example .env

然后编辑 `.env`，填入自己的 DeepSeek API Key：

    DEEPSEEK_API_KEY=你的_DeepSeek_API_Key
    DEEPSEEK_MODEL=deepseek-v4-flash
    DEEPSEEK_BASE_URL=https://api.deepseek.com

`.env` 已被 `.gitignore` 忽略，不应提交到 Git 或 GitHub。

## 运行项目

生成 pandas 数据摘要：

    python src/data_summary.py

进行第一次非流式 API 调用：

    python src/llm_client.py

运行 V1 Prompt 对照实验：

    python src/prompt_runner.py v1

运行 V2 Prompt 对照实验：

    python src/prompt_runner.py v2

生成正常的结构化解读：

    python src/interpreter.py

生成“证据不足”的结构化解读：

    python src/interpreter.py insufficient-evidence

注意：两次运行 `interpreter.py` 都会写入 `outputs/structured-result.json`。项目中已分别备份成功结果和证据不足结果。

## 测试

执行离线测试：

    python -m pytest tests/ -v

最终结果：

    4 passed

四个测试均使用假客户端或本地数据，不访问真实 DeepSeek API，也不需要真实 API Key。

## 示例输出

`outputs/summary.json` 包含总行数、缺失数，以及每个工作类型的样本数和平均血糖水平。

结构化结果包含以下固定字段：

    {
      "conclusion": "...",
      "evidence": [
        {"metric": "...", "value": "..."}
      ],
      "limitations": ["..."],
      "next_step": "..."
    }

## 辅助脚本说明

`src/list_models.py` 是项目早期使用 OpenAI 时编写的模型列表检查脚本。它依赖旧版 OpenAI 配置，不适用于当前 DeepSeek 改编版，因此不属于本项目的运行流程。

## 已知限制

- 数据摘要只包含 `work_type` 和 `avg_glucose_level` 的聚合信息。
- 类别间平均值不同不代表存在因果关系。
- Pydantic 能保证结构和字段类型，证据值检查能核对 `evidence.value` 是否存在于摘要中，但不能自动保证所有自然语言结论都完全没有越界。
- Prompt 可以降低模型补充背景、单位或因果解释的概率，但仍需要人工审查。
- DeepSeek 改编版不具备 OpenAI Responses API 的原生 `output_parsed` 功能。