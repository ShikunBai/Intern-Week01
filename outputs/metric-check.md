# 指标复核记录

## 复核目标

复核 `Govt_job` 类别的样本数和平均血糖水平。

## pandas 摘要结果

来自 `outputs/summary.json`：

- 类别：`Govt_job`
- 样本数：657
- 平均血糖水平：107.78

## R 独立复核

使用 R 直接读取原始文件 `data/stroke_data.csv`，运行：

    Rscript -e 'd <- read.csv("data/stroke_data.csv"); x <- d$avg_glucose_level[d$work_type == "Govt_job"]; cat("样本数:", length(x), "\n平均血糖水平:", mean(x), "\n")'

输出：

    样本数: 657
    平均血糖水平: 107.7798

## 结论

R 计算得到的样本数为 657，与 pandas 摘要一致。

R 计算得到的平均血糖水平为 107.7798；四舍五入保留两位小数后为 107.78，与 `summary.json` 一致。因此，摘要中的该类别计算结果通过独立复核。
