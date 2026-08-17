import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_summary import build_summary


def test_summary_contains_correct_group_metrics():
    """验证 Govt_job 的样本数与平均血糖水平。"""
    summary = build_summary()

    groups = {
        group["类别"]: group
        for group in summary["类别汇总"]
    }

    govt_job = groups["Govt_job"]

    assert summary["总行数"] == 5110
    assert summary["缺失数"]["work_type"] == 0
    assert summary["缺失数"]["avg_glucose_level"] == 0
    assert govt_job["样本数"] == 657
    assert govt_job["平均血糖水平"] == 107.78
