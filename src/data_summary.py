import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "stroke_data.csv"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "summary.json"

CATEGORY_COLUMN = "work_type"
NUMERIC_COLUMN = "avg_glucose_level"


def build_summary() -> dict:
    """读取 CSV，并生成可复核的数据摘要。"""
    dataframe = pd.read_csv(DATA_PATH)

    required_columns = {CATEGORY_COLUMN, NUMERIC_COLUMN}
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        raise ValueError(f"CSV 缺少必要字段：{sorted(missing_columns)}")

    numeric_values = pd.to_numeric(dataframe[NUMERIC_COLUMN], errors="coerce")
    working_data = dataframe.assign(metric_value=numeric_values)

    grouped = (
        working_data.dropna(subset=[CATEGORY_COLUMN, "metric_value"])
        .groupby(CATEGORY_COLUMN, sort=True)["metric_value"]
        .agg(sample_count="size", mean_value="mean")
        .reset_index()
    )

    groups = [
        {
            "类别": str(row[CATEGORY_COLUMN]),
            "样本数": int(row["sample_count"]),
            "平均血糖水平": round(float(row["mean_value"]), 2),
        }
        for _, row in grouped.iterrows()
    ]

    return {
        "分析主题": "不同工作类型的平均血糖水平和样本量有什么差异？",
        "数据文件": "data/stroke_data.csv",
        "总行数": int(len(dataframe)),
        "相关字段": {
            "类别字段": CATEGORY_COLUMN,
            "数值字段": NUMERIC_COLUMN,
        },
        "缺失数": {
            CATEGORY_COLUMN: int(dataframe[CATEGORY_COLUMN].isna().sum()),
            NUMERIC_COLUMN: int(numeric_values.isna().sum()),
        },
        "类别汇总": groups,
        "计算说明": "每个类别的样本量和平均值仅基于类别字段与数值字段均非缺失的记录。",
    }


def main() -> None:
    summary = build_summary()

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print(f"摘要已保存：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
