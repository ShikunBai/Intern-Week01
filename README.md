# Data Summary Interpreter

本项目是第 1 周的学习作业。

程序将使用 pandas 计算一份小型 CSV 数据的确定性摘要，再使用 OpenAI Responses API 生成一份有证据约束的结构化解读。

## 当前进度

- 已创建项目目录和 Python 虚拟环境
- 已安装 openai、pandas、pydantic、python-dotenv、pytest
- 已完成 `src/llm_client.py`，并验证缺少 API 配置时的受控错误
- 已完成 pandas 数据摘要、`summary.json` 和 R 独立复核
- 待完成：解决 API 的 429 问题并保存真实模型响应
- 已完成 编写 V1 与 V2 Prompt 文件
- 下一步：解决 API 的 429 问题后，依次运行 V1 和 V2 Prompt 实验，保存两份真实模型输出，并从事实准确性、证据引用、限制说明和多余推断四个维度完成对比

## 辅助脚本

`src/list_models.py` 用于检查当前 API Key 可访问的模型列表。运行该脚本需要有效的 `.env` 配置和网络连接；它不会在代码或输出中保存 API Key。

## 数据来源与字段含义

本项目使用 `data/stroke_data.csv`。

- 数据集名称：Stroke Prediction Dataset（中风预测数据集）
- 原始发布页：<https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset>
- `work_type`：类别字段，表示工作类型。
- `avg_glucose_level`：数值字段，表示平均血糖水平。

## 安装

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/data_summary.py
```